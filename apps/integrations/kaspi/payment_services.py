from constance import config

from apps.integrations.kaspi.base import BaseKaspiService
from apps.payments import PaymentProviders
from apps.payments.models import Payment


class KaspiRetrievePaymentDeeplinkService(BaseKaspiService):
    endpoint = "/online"
    instance: 'Booking'
    method = "POST"
    save_serializer = None
    log_request = True
    log_response = True

    def run_service(self):
        # TODO: Initialize Payment with PaymentStatuses.CREATED status
        payment = Payment.objects.create(
            booking=self.instance,
            user=self.instance.club_user.user,
            amount=self.instance.total_amount,
            provider=PaymentProviders.KASPI
        )
        return self.fetch(json={
            "TranId": str(payment.uuid),
            "OrderId": str(self.instance.uuid),
            "Amount": int(payment.amount*100),
            "Service": config.KASPI_PAYMENT_SERVICE_CODE,
            "returnUrl": config.KASPI_PAYMENT_DEEPLINK_HOST,
            "refererHost": "server.gamerpro.kz",
            "GenerateQrCode": False
        })

    def finalize_response(self, response):
        if response and response.get('code') == 0:
            return response.get('redirectUrl')
