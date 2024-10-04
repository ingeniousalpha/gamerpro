from constance import config

from apps.integrations.kaspi.base import BaseKaspiService


class KaspiRetrievePaymentDeeplinkService(BaseKaspiService):
    endpoint = "/online"
    instance: 'Booking'
    save_serializer = None

    def run_service(self):
        return self.fetch(data={
            "TranId": "212695001",
            "OrderId": str(self.instance.uuid),
            "Amount": int(self.instance.total_amount*100),
            "Service": config.KASPI_PAYMENT_SERVICE_CODE,
            "returnUrl": config.KASPI_PAYMENT_DEEPLINK_HOST,
            "refererHost": "server.gamerpro.kz",
            "GenerateQrCode": False
        })

    def finalize_response(self, response):
        if response and response.get('code') == 0:
            return response.get('redirectUrl')
