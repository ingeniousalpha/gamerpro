from django.db import transaction
from django.utils import timezone
from constance import config
from rest_framework import serializers

from apps.authentication.exceptions import UserNotFound
from apps.bookings.models import Booking, BookedComputer
from apps.bookings.tasks import gizmo_book_computers
from apps.clubs.exceptions import ComputerDoesNotBelongToClubBranch, ComputerIsAlreadyBooked
from apps.clubs.models import ClubComputer
from apps.clubs.serializers import ClubBranchSerializer, ClubComputerListSerializer
from apps.common.serializers import RequestUserPropertyMixin
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
        club_user = self.user.get_club_accont(attrs['club_branch'])
        if not club_user:
            raise UserNotFound
        attrs['club_user'] = club_user

        computers = []
        for computer_id in attrs.pop('computers'):
            computer = attrs['club_branch'].computers.filter(id=computer_id).first()
            if not computer:
                raise ComputerDoesNotBelongToClubBranch
            if computer.is_booked:
                raise ComputerIsAlreadyBooked
            computers.append(computer)

        attrs['computers'] = computers
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
            self.extra_task(booking, validated_data)

        return booking


class CreateBookingByBalanceSerializer(BaseCreateBookingSerializer):

    def extra_task(self, instance, validated_data):
        if config.INTEGRATIONS_TURNED_ON:
            gizmo_book_computers(str(instance.uuid))

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
                gizmo_book_computers(str(instance.uuid))
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
        status, error = OVRecurrentPaymentService(instance=instance).run()
        if error:
            raise OVRecurrentPaymentFailed(error)
        if config.INTEGRATIONS_TURNED_ON:
            gizmo_book_computers(str(instance.uuid))
        self.context['status'] = status

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


class BookingListSerializer(serializers.ModelSerializer):
    club_branch = ClubBranchSerializer()
    computers = BookedComputerListSerializer(many=True)

    class Meta:
        model = Booking
        fields = (
            'uuid',
            'created_at',
            'club_branch',
            'amount',
            'computers'
        )