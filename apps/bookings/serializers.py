from decimal import Decimal
from constance import config
from rest_framework import serializers
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from apps.authentication.exceptions import UserNotFound
from apps.bookings.models import Booking, BookedComputer
from apps.bookings.tasks import gizmo_book_computers, gizmo_lock_computers
from apps.clubs.exceptions import ComputerDoesNotBelongToClubBranch, ComputerIsAlreadyBooked
from apps.clubs.models import ClubComputer
from apps.clubs.serializers import ClubBranchSerializer, ClubComputerListSerializer
from apps.common.serializers import RequestUserPropertyMixin
from apps.payments import PAYMENT_STATUSES_MAPPER, PaymentStatuses
from apps.payments.exceptions import OVRecurrentPaymentFailed
from apps.integrations.onevision.payer_services import OVCreatePayerService
from apps.integrations.onevision.payment_services import OVInitPaymentService, OVRecurrentPaymentService


class BaseCreateBookingSerializer(
    RequestUserPropertyMixin,
    serializers.ModelSerializer
):
    computers = serializers.ListField(write_only=True)

    class Meta:
        model = Booking
        fields = (
            'club_branch',
            'computers',
        )

    def validate(self, attrs):
        print(attrs)
        club_user = self.user.get_club_account(attrs['club_branch'])
        if not club_user:
            raise UserNotFound
        attrs['club_user'] = club_user

        computers = []
        for computer_id in attrs.pop('computers'):
            computer = attrs['club_branch'].computers.filter(id=computer_id).first()
            if not computer:
                raise ComputerDoesNotBelongToClubBranch
            if computer.is_booked or cache.get(f'BOOKING_STATUS_COMP_{computer_id}', False):
                raise ComputerIsAlreadyBooked
            computers.append(computer)

        attrs['computers'] = computers
        amount = attrs.get('amount', Decimal(0))
        attrs['commission_amount'] = Booking.get_commission_amount(amount)
        attrs['total_amount'] = attrs['commission_amount'] + amount
        return attrs

    def extra_task(self, instance, validated_data):
        ...

    def create(self, validated_data):
        with transaction.atomic():
            computers = validated_data.pop('computers')
            expiration_date = timezone.now() + timezone.timedelta(minutes=config.PAYMENT_EXPIRY_TIME)
            validated_data['expiration_date'] = expiration_date
            booking = super().create(validated_data)
            for computer in computers:
                BookedComputer.objects.create(booking=booking, computer=computer)
                cache.set(f'BOOKING_STATUS_COMP_{computer.id}', True, config.PAYMENT_EXPIRY_TIME*60)
            self.extra_task(booking, validated_data)
            booking.refresh_from_db()

        return booking


class CreateBookingByBalanceSerializer(BaseCreateBookingSerializer):

    def extra_task(self, instance, validated_data):
        instance.use_balance = True
        instance.save()
        if config.INTEGRATIONS_TURNED_ON:
            gizmo_book_computers(str(instance.uuid), from_balance=True)

    def to_representation(self, instance):
        return {
            "booking_uuid": str(instance.uuid)
        }


class CreateBookingByPaymentSerializer(BaseCreateBookingSerializer):
    class Meta(BaseCreateBookingSerializer.Meta):
        fields = BaseCreateBookingSerializer.Meta.fields + ('amount',)

    def extra_task(self, instance, validated_data):
        if not instance.club_user.user.outer_payer_id:
            OVCreatePayerService(instance=instance.club_user.user).run()
        payment_url = OVInitPaymentService(instance=instance).run()
        if payment_url:
            if config.INTEGRATIONS_TURNED_ON:
                gizmo_lock_computers(str(instance.uuid))
            self.context['payment_url'] = payment_url
        else:
            raise Exception

    def to_representation(self, instance):
        return {
            "booking_uuid": str(instance.uuid),
            "payment_url": self.context['payment_url']
        }


class CreateBookingByCardPaymentSerializer(BaseCreateBookingSerializer):
    class Meta(BaseCreateBookingSerializer.Meta):
        fields = BaseCreateBookingSerializer.Meta.fields + (
            'amount',
            'payment_card'
        )

    def extra_task(self, instance, validated_data):
        if not instance.club_user.user.outer_payer_id:
            OVCreatePayerService(instance=instance.club_user.user).run()
        payment, error = OVRecurrentPaymentService(instance=instance).run()
        if error:
            raise OVRecurrentPaymentFailed(error)
        if config.INTEGRATIONS_TURNED_ON:
            gizmo_book_computers(str(instance.uuid))
        self.context['status'] = PAYMENT_STATUSES_MAPPER.get(int(payment.status))

    def to_representation(self, instance):
        return {
            "booking_uuid": str(instance.uuid),
            "status": self.context['status']
        }


class BookedComputerListSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='computer.id')
    number = serializers.IntegerField(source='computer.number')
    hall_name = serializers.CharField(source='computer.group.name')

    class Meta:
        model = BookedComputer
        fields = (
            'id',
            'number',
            'hall_name',
        )


class BookingSerializer(serializers.ModelSerializer):
    club_branch = ClubBranchSerializer()
    computers = BookedComputerListSerializer(many=True)
    payment_status = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = (
            'uuid',
            'created_at',
            'club_branch',
            'amount',
            'is_active',
            'status',
            'payment_status',
            'computers'
        )

    def get_payment_status(self, obj):
        if obj.payments.exists():
            return PAYMENT_STATUSES_MAPPER.get(int(obj.payments.last().status))
        elif obj.use_balance:
            return "BALANCE_APPROVED"
        return "NOT_PAID"
