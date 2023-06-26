import base64
import json

from apps.payments import PaymentStatuses
from apps.payments.serializers import SavePaymentSerializer
from apps.bookings.models import Booking
from apps.payments.models import PaymentWebhook


def b64_encode(raw_data: dict) -> str:
    return base64.b64encode(
        json.dumps(raw_data).encode('utf-8')
    ).decode('ascii')


def b64_decode(encoded_data: str) -> dict:
    return json.loads(
        base64.b64decode(encoded_data.encode('utf-8')).decode('utf-8')
    )


def split_card_numbers(card_number):
    if card_number is None:
        return "", ""
    return card_number[:6], card_number[-4:]


def handle_ov_response(webhook_data, is_webhook=True):
    if is_webhook:
        webhook, created = PaymentWebhook.objects.get_or_create(
            transaction_id=webhook_data['transaction_id'],
            booking_uuid=webhook_data['reference'],
            data=webhook_data
        )
        if not created and webhook.payment:
            return

    booking = Booking.objects.filter(uuid=webhook_data['reference']).first()
    if not booking:
        return

    payment_card = {}
    if not booking.payment_card:
        first_numbers, last_numbers = split_card_numbers(webhook_data.get('card_number'))
        payment_card = {
            'pay_token': webhook_data.get('pay_token'),
            'card_type': webhook_data.get('card_type'),
            'user': booking.club_user.user.id,
            'first_numbers': first_numbers,
            'last_numbers': webhook_data.get('card_pan4'),
        }
    serializer = SavePaymentSerializer(data={
        'outer_id': webhook_data['transaction_id'],
        'amount': webhook_data['amount'],
        'booking': booking.id,
        'user': booking.club_user.user.id,
        'payment_card': payment_card
    })
    serializer.is_valid(raise_exception=True)
    payment = serializer.save()

    if str(webhook_data['status']) == PaymentStatuses.CREATED:
        pass
    elif str(webhook_data['status']) == PaymentStatuses.AUTH:
        pass
    elif str(webhook_data['status']) == PaymentStatuses.VOID:
        pass
    elif str(webhook_data['status']) == PaymentStatuses.REFUND_APPROVED:
        pass

    elif str(webhook_data['status']) == PaymentStatuses.PAYMENT_APPROVED:
        payment.move_to_approved()
        payment.user.set_current_card(payment.card)

    elif str(webhook_data['status']) == PaymentStatuses.IN_PROGRESS:
        payment.move_to_in_progress()

    elif str(webhook_data['status']) == PaymentStatuses.FAILED:
        payment.move_to_failed(
            f"{webhook_data.get('internal_error_reference')}|{webhook_data['processing_error_msg']}"
        )
        # booking.cancel()

    if is_webhook:
        webhook.payment = payment
        webhook.save()
