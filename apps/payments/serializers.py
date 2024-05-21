from django.db import transaction
from rest_framework import serializers
from decimal import Decimal

from constance import config
from apps.bookings.exceptions import BookingNotFound
from apps.bookings.models import DepositReplenishment, Booking
from apps.common.serializers import RequestUserPropertyMixin
from apps.integrations.onevision.payment_services import OVRecurrentPaymentService
from apps.payments.exceptions import OVRecurrentPaymentFailed
from apps.payments.models import Payment, PaymentCard
from apps.integrations.gizmo.deposits_services import GizmoCreateDepositTransactionService
from apps.integrations.gizmo.time_packets_services import GizmoAddPaidTimeToUser, GizmoSetTimePacketToUser


class PaymentCardListSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentCard
        fields = (
            'id',
            'masked_number',
            'is_current'
        )


class DepositReplenishmentSerializer(RequestUserPropertyMixin, serializers.ModelSerializer):
    amount = serializers.DecimalField(
        write_only=True,
        decimal_places=2,
        max_digits=8,
        source='user_received_amount'
    )

    class Meta:
        model = DepositReplenishment
        fields = (
            'club_branch',
            'amount',
            'payment_card',
        )

    def create(self, validated_data):
        commission_amount = Booking.get_commission_amount(validated_data['user_received_amount'])
        total_amount = commission_amount + validated_data['user_received_amount']
        payment, error = OVRecurrentPaymentService(
            club_branch=validated_data['club_branch'],
            is_replenishment=True,
            total_amount=total_amount,
            pay_token=validated_data['payment_card'].pay_token,
            outer_payer_id=self.user.outer_payer_id,
        ).run()
        if error:
            raise OVRecurrentPaymentFailed(error)
        replenishment = GizmoCreateDepositTransactionService(
            instance=validated_data['club_branch'],
            user_received_amount=validated_data['user_received_amount'],
            commission_amount=commission_amount,
            total_amount=total_amount,
            user_gizmo_id=self.user.get_club_account(validated_data['club_branch']).gizmo_id,
            payment_card=validated_data['payment_card']
        ).run()
        payment.replenishment = replenishment
        payment.save()
        return replenishment


class BookingProlongSerializer(RequestUserPropertyMixin, serializers.ModelSerializer):

    class Meta:
        model = DepositReplenishment
        fields = (
            'club_branch',
            'amount',
            'payment_card',
            'booking',
            'time_packet',
        )
        extra_kwargs = {
            "time_packet": {"required": False}
        }

    def create(self, validated_data):
        commission_amount = Booking.get_commission_amount(validated_data['amount'])
        total_amount = commission_amount + validated_data['amount']
        payment, error = OVRecurrentPaymentService(
            club_branch=validated_data['club_branch'],
            is_replenishment=True,
            replenishment_reference=validated_data.get('booking').uuid,
            total_amount=total_amount,
            pay_token=validated_data['payment_card'].pay_token,
            outer_payer_id=self.user.outer_payer_id,
        ).run()
        if error:
            raise OVRecurrentPaymentFailed(error)
        replenishment = GizmoCreateDepositTransactionService(
            instance=validated_data['club_branch'],
            amount=validated_data['amount'],
            commission_amount=commission_amount,
            total_amount=total_amount,
            user_gizmo_id=self.user.get_club_account(validated_data['club_branch']).gizmo_id,
            payment_card=validated_data['payment_card'],
            booking=validated_data.get('booking')
        ).run()
        payment.replenishment = replenishment
        payment.save()
        return replenishment


class BookingProlongByTimePacketSerializer(RequestUserPropertyMixin, serializers.ModelSerializer):

    class Meta:
        model = DepositReplenishment
        fields = (
            'payment_card',
            'booking',
            'time_packet',
        )

    def validate(self, attrs):
        commission_amount = Booking.get_commission_amount(attrs['time_packet'].price)
        total_amount = commission_amount + Decimal(attrs['time_packet'].price)
        attrs['club_branch'] = attrs['booking'].club_branch
        attrs['club_user'] = attrs['booking'].club_user
        attrs['commission_amount'] = commission_amount
        attrs['total_amount'] = total_amount
        return attrs

    def create(self, validated_data):
        payment, error = OVRecurrentPaymentService(
            club_branch=validated_data['club_branch'],
            is_replenishment=True,
            replenishment_reference=validated_data.get('booking').uuid,
            total_amount=validated_data['total_amount'],
            pay_token=validated_data['payment_card'].pay_token,
            outer_payer_id=validated_data['club_user'].onevision_payer_id,
        ).run()
        if error:
            raise OVRecurrentPaymentFailed(error)

        replenishment = super().create(validated_data)

        GizmoSetTimePacketToUser(
            instance=validated_data['club_branch'],
            user_id=validated_data['booking'].club_user.gizmo_id,
            product_id=validated_data['time_packet'].gizmo_id
        ).run()
        payment.replenishment = replenishment
        payment.save()
        if config.CASHBACK_TURNED_ON:
            GizmoCreateDepositTransactionService(
                instance=validated_data['booking'].club_branch,
                user_gizmo_id=validated_data['booking'].club_user.gizmo_id,
                booking=validated_data['booking'],
                user_received_amount=validated_data['booking'].amount,
                commission_amount=validated_data['booking'].commission_amount,
                total_amount=validated_data['booking'].total_amount,
                replenishment_type="cashback",
            ).run()
        return replenishment
