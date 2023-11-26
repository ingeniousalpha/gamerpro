from django.db import transaction
from rest_framework import serializers

from apps.bookings.exceptions import BookingNotFound
from apps.bookings.models import DepositReplenishment, Booking
from apps.common.serializers import RequestUserPropertyMixin
from apps.integrations.onevision.payment_services import OVRecurrentPaymentService
from apps.payments.exceptions import OVRecurrentPaymentFailed
from apps.payments.models import Payment, PaymentCard
from apps.integrations.gizmo.deposits_services import GizmoCreateDepositTransactionService


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
        commission_amount = Booking.get_commission_amount(validated_data['amount'])
        total_amount = commission_amount + validated_data['amount']
        payment, error = OVRecurrentPaymentService(
            is_replenishment=True,
            total_amount=total_amount,
            pay_token=validated_data['payment_card'].pay_token,
            outer_payer_id=self.user.outer_payer_id,
        ).run()
        if error:
            raise OVRecurrentPaymentFailed(error)
        replenishment = GizmoCreateDepositTransactionService(
            instance=validated_data['club_branch'],
            user_received_amount=validated_data['amount'],
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
        )

    def create(self, validated_data):
        commission_amount = Booking.get_commission_amount(validated_data['amount'])
        total_amount = commission_amount + validated_data['amount']
        payment, error = OVRecurrentPaymentService(
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
