import json

from django.contrib.auth import get_user_model

from apps.bookings import BookingStatuses
from apps.bookings.tasks import gizmo_book_computers, send_push_about_booking_status, gizmo_bro_book_computers
from apps.payments import PaymentStatuses
from apps.integrations.onevision.serializers import SavePaymentSerializer
from apps.bookings.models import Booking
from apps.payments.models import PaymentWebhook

User = get_user_model()


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

    if isinstance(webhook_data['params'], str):
        outer_payer_id = json.loads(webhook_data['params'].replace('=>', ':'))['user_id']
    else:
        outer_payer_id = webhook_data['params']['user_id']

    booking_uuid = None
    user = User.objects.filter(outer_payer_id=outer_payer_id).first()
    payment_data = {
        'outer_id': webhook_data['transaction_id'],
        'amount': webhook_data['amount'],
        'user': user.id,
        'payment_card': {}
    }
    if "REPLENISHMENT" in webhook_data.get('description', {}):
        payment_data['uuid'] = webhook_data['reference']
        if len(reference := webhook_data['description'].split("_")) > 1:
            booking_uuid = reference[-1]
    else:
        booking_uuid = webhook_data['reference']

    if booking_uuid:
        booking = Booking.objects.filter(uuid=booking_uuid).first()
        if not booking:
            return
        payment_data['booking'] = booking.id

    if webhook_data.get('card_number'):
        first_numbers, last_numbers = split_card_numbers(webhook_data.get('card_number'))
        payment_data['payment_card'] = {
            'pay_token': webhook_data.get('pay_token'),
            'card_type': webhook_data.get('card_type'),
            'user': user.id,
            'first_numbers': first_numbers,
            'last_numbers': webhook_data.get('card_pan4'),
        }
    serializer = SavePaymentSerializer(data=payment_data)
    if booking_uuid:
        booking.refresh_from_db()
    serializer.is_valid()
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
        if booking_uuid and not booking.payment_card and not booking.use_balance:
            if booking.club_branch.club.name.lower() == "bro" and booking.club_user.is_verified:
                gizmo_bro_book_computers(booking_uuid)
            elif booking.club_branch.club.name.lower() != "bro":
                gizmo_book_computers(booking_uuid)
                send_push_about_booking_status.delay(booking.uuid, BookingStatuses.ACCEPTED)  # booking by new payment accepted

    elif str(webhook_data['status']) == PaymentStatuses.IN_PROGRESS:
        payment.move_to_in_progress()

    elif str(webhook_data['status']) == PaymentStatuses.FAILED:
        payment.move_to_failed(
            f"{webhook_data.get('internal_error_reference')}|{webhook_data.get('processing_error_msg')}"
        )
        # booking.cancel()

    if is_webhook:
        webhook.payment = payment
        webhook.save()

    return payment
