import logging
from decimal import Decimal
from constance import config
from rest_framework import serializers
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from apps.authentication.exceptions import UserNotFound, UserAlreadyHasActiveBooking, \
    NotApprovedUserCanNotBookSeveralComputers, NotSufficientCashbackAmount
from apps.bookings import BookingStatuses
from apps.bookings.models import Booking, BookedComputer
from apps.bookings.tasks import gizmo_book_computers, gizmo_lock_computers, send_push_about_booking_status, \
    gizmo_bro_add_time_and_set_booking_expiration
from apps.clubs.exceptions import ComputerDoesNotBelongToClubBranch, ComputerIsAlreadyBooked
from apps.clubs.serializers import ClubBranchSerializer
from apps.clubs.services import get_cashback
from apps.common.serializers import RequestUserPropertyMixin
from apps.common.services import date_format_with_t
from apps.integrations.kaspi.exceptions import KaspiServiceError
from apps.integrations.kaspi.payment_services import KaspiRetrievePaymentDeeplinkService
from apps.payments import PAYMENT_STATUSES_MAPPER, PaymentStatuses
from apps.payments.exceptions import OVRecurrentPaymentFailed
from apps.integrations.onevision.payer_services import OVCreatePayerService
from apps.integrations.onevision.payment_services import OVInitPaymentService, OVRecurrentPaymentService

logger = logging.getLogger("onevision")


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
        if club_user.has_active_booking:
            raise UserAlreadyHasActiveBooking
        if not club_user.is_verified and len(attrs['computers']) > 1:
            raise NotApprovedUserCanNotBookSeveralComputers
        if self.context.get('booking_method') == 'by_cashback':
            if get_cashback(club_user.user, club_user.club_branch.club) < attrs['time_packet'].price:
                raise NotSufficientCashbackAmount

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
        if attrs.get('time_packet'):
            amount = attrs['time_packet'].price
        else:
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
                if 'payment_card' not in validated_data:
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
        send_push_about_booking_status.delay(instance.uuid, BookingStatuses.ACCEPTED)  # booking by balance accepted

    def to_representation(self, instance):
        return {
            "booking_uuid": str(instance.uuid)
        }


class CreateBookingByPaymentSerializer(BaseCreateBookingSerializer):
    class Meta(BaseCreateBookingSerializer.Meta):
        fields = BaseCreateBookingSerializer.Meta.fields + ('amount',)

    def extra_task(self, instance, validated_data):
        # TODO: refactor to respond error when error happens
        try:
            if not instance.club_user.onevision_payer_id:
                OVCreatePayerService(
                    instance=instance.club_user.user,
                    club_branch=instance.club_branch,
                ).run()
            payment_url = OVInitPaymentService(
                instance=instance,
                club_branch=instance.club_branch,
            ).run()
            if payment_url:
                if config.INTEGRATIONS_TURNED_ON:
                    gizmo_lock_computers(str(instance.uuid))
                self.context['payment_url'] = payment_url
            else:
                raise Exception("There is no payment_url")
        except Exception as e:
            logger.error(f"CreateBookingByPaymentSerializer Error: {str(e)}")

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
        try:
            if not instance.club_user.onevision_payer_id:
                OVCreatePayerService(
                    instance=instance.club_user.user,
                    club_branch=instance.club_branch,
                ).run()
            payment, error = OVRecurrentPaymentService(
                instance=instance,
                club_branch=instance.club_branch,
            ).run()
            if error:
                raise OVRecurrentPaymentFailed(error)
            if config.INTEGRATIONS_TURNED_ON:
                if instance.club_branch.club.name.lower() == "bro":
                    gizmo_lock_computers(str(instance.uuid))
                    if instance.club_user.is_verified:
                        gizmo_bro_add_time_and_set_booking_expiration.delay(str(instance.uuid))
                else:
                    gizmo_book_computers(str(instance.uuid))
            self.context['status'] = PAYMENT_STATUSES_MAPPER.get(int(payment.status))
            send_push_about_booking_status.delay(instance.uuid, BookingStatuses.ACCEPTED)  # booking by card payment accepted
        except Exception as e:
            logger.error(f"CreateBookingByCardPaymentSerializer Error: {str(e)}")

    def to_representation(self, instance):
        return {
            "booking_uuid": str(instance.uuid),
            "status": self.context['status']
        }


class CreateBookingByCashbackSerializer(BaseCreateBookingSerializer):
    class Meta(BaseCreateBookingSerializer.Meta):
        fields = BaseCreateBookingSerializer.Meta.fields + (
            'amount',
            'time_packet',
        )

    def extra_task(self, instance, validated_data):
        try:
            instance.use_cashback = True
            instance.save()
            if config.INTEGRATIONS_TURNED_ON:
                if instance.club_branch.club.name.lower() == "bro":
                    gizmo_lock_computers(str(instance.uuid))
                    if instance.club_user.is_verified:
                        gizmo_bro_add_time_and_set_booking_expiration.delay(str(instance.uuid), by_points=True)
                else:
                    # TODO: this need to check is it working
                    gizmo_book_computers(str(instance.uuid))
            send_push_about_booking_status.delay(instance.uuid, BookingStatuses.ACCEPTED)
        except Exception as e:
            logger.error(f"CreateBookingByCashbackSerializer Error: {str(e)}")
            raise e

    def to_representation(self, instance):
        return {
            "booking_uuid": str(instance.uuid)
        }


class CreateBookingByTimePacketPaymentSerializer(CreateBookingByPaymentSerializer):
    class Meta(CreateBookingByPaymentSerializer.Meta):
        fields = CreateBookingByPaymentSerializer.Meta.fields + ('time_packet',)


class CreateBookingByTimePacketKaspiSerializer(CreateBookingByPaymentSerializer):
    class Meta(CreateBookingByPaymentSerializer.Meta):
        fields = CreateBookingByPaymentSerializer.Meta.fields + ('time_packet',)

    def extra_task(self, instance, validated_data):
        try:
            deeplink_url = KaspiRetrievePaymentDeeplinkService(
                instance=instance,
                club_branch=instance.club_branch,
            ).run()
            if deeplink_url:
                if config.INTEGRATIONS_TURNED_ON:
                    gizmo_lock_computers(str(instance.uuid))
                self.context['payment_url'] = deeplink_url
            else:
                raise Exception("There is no payment_url")
        except Exception as e:
            logger.error(f"CreateBookingByTimePacketKaspiSerializer Error: {str(e)}")
            raise KaspiServiceError


class CreateBookingByTimePacketCardPaymentSerializer(CreateBookingByCardPaymentSerializer):
    class Meta(CreateBookingByCardPaymentSerializer.Meta):
        fields = CreateBookingByCardPaymentSerializer.Meta.fields + ('time_packet',)


class BookedComputerListSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='computer.id')
    number = serializers.IntegerField(source='computer.number')
    hall_name = serializers.SerializerMethodField()
    hall_id = serializers.SerializerMethodField()

    class Meta:
        model = BookedComputer
        fields = (
            'id',
            'number',
            'hall_name',
            'hall_id',
        )

    def get_hall_name(self, obj):
        if obj.computer.group:
            return obj.computer.group.name
        return ""

    def get_hall_id(self, obj):
        if obj.computer.group:
            return obj.computer.group.id
        return 0


class BookingSerializer(serializers.ModelSerializer):
    club_branch = ClubBranchSerializer()
    computers = BookedComputerListSerializer(many=True)
    payment_status = serializers.SerializerMethodField()
    session_starting_at = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = (
            'uuid',
            'session_starting_at',
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
        elif obj.use_cashback:
            return "CASHBACK_APPROVED"
        return "NOT_PAID"

    def get_session_starting_at(self, obj):
        return date_format_with_t(
            obj.created_at + timezone.timedelta(seconds=config.FREE_SECONDS_BEFORE_START_TARIFFING)
        )
