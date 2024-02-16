from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from apps.clubs.models import Club, ClubBranchLegalEntity
from apps.payments.models import PaymentCard, Payment
from apps.users.models import UserOneVisionPayer

User = get_user_model()


class OVSavePayerIDSerializer(serializers.ModelSerializer):
    trader_code = serializers.CharField()
    outer_payer_id = serializers.CharField()

    class Meta:
        model = User
        fields = (
            'outer_payer_id',
            'trader_code'
        )

    def update(self, instance, validated_data):
        UserOneVisionPayer.objects.get_or_create(
            user=instance,
            trader=ClubBranchLegalEntity.objects.get(code=validated_data['trader_code']),
            defaults={
                "payer_id": validated_data['outer_payer_id']
            }
        )
        return instance


class SavePaymentSerializer(serializers.ModelSerializer):
    payment_card = serializers.JSONField(required=False)
    uuid = serializers.UUIDField(required=False)

    class Meta:
        model = Payment
        fields = (
            'uuid',
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

            if card := PaymentCard.objects.filter(pay_token=payment_card.get('pay_token') or "no_card").first():
                payment.card = card
                payment.save(update_fields=['card'])
                if payment.booking:
                    payment.booking.payment_card = card
                    payment.booking.save(update_fields=['payment_card'])

            if not payment.card and payment_card and payment_card.get('last_numbers'):
                serializer = SavePaymentCardSerializer(data=payment_card)
                serializer.is_valid(raise_exception=True)
                card = serializer.save()
                payment.card = card
                payment.save(update_fields=['card'])
                if payment.booking:
                    payment.booking.payment_card = card
                    payment.booking.save(update_fields=['payment_card'])
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
