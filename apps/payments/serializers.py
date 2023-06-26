from django.db import transaction
from rest_framework import serializers

from apps.payments.models import Payment, PaymentCard


class SavePaymentSerializer(serializers.ModelSerializer):
    payment_card = serializers.JSONField(required=False)

    class Meta:
        model = Payment
        fields = (
            'outer_id',
            'amount',
            'booking',
            'user',
            'payment_card',
        )
        extra_kwargs = {
            'outer_id': {'validators': []},
            'booking': {'validators': []}
        }

    def create(self, validated_data):
        with transaction.atomic():
            payment_card = validated_data.pop('payment_card')

            payment = self.Meta.model.objects.filter(outer_id=validated_data['outer_id']).first()
            if not payment:
                payment = super().create(validated_data)

            if payment.booking.payment_card:
                payment.card = payment.booking.payment_card
                payment.save(update_fields=['card'])

            if not payment.card and payment_card and payment_card.get('last_numbers'):
                serializer = SavePaymentCardSerializer(data=payment_card)
                serializer.is_valid(raise_exception=True)
                card = serializer.save()
                payment.card = card
                payment.save()
            return payment


class SavePaymentCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentCard
        fields = (
            'pay_token',
            'user',
            'is_current',
            'first_numbers',
            'last_numbers',
        )


class PaymentCardListSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentCard
        fields = (
            'id',
            'masked_number',
            'is_current'
        )
