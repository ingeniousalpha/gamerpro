import uuid
from django.conf import settings

from apps.common.services import date_format
from apps.payments import PAYMENT_STATUSES_MAPPER
from apps.payments.services import b64_decode, handle_ov_response
from apps.integrations.onevision.base import BaseOneVisionService


class OVInitPaymentService(BaseOneVisionService):
    """Оплата новой картой"""

    endpoint = "/pay"
    method = "POST"
    save_serializer = None
    instance: 'Booking'

    def run_service(self):
        return self.fetch(data=self.form_encoded_data({
            "api_key": settings.ONE_VISION_API_KEY,
            "expiration": date_format(self.instance.expiration_date),
            "amount": str(self.instance.amount),
            "currency": "KZT",
            "description": "Оплата брони",
            "reference": str(self.instance.uuid),
            "success_url": f"{settings.SITE_DOMAIN}/api/payments/success?booking_uuid={str(self.instance.uuid)}",
            "failure_url": f"{settings.SITE_DOMAIN}/api/payments/fail?booking_uuid={str(self.instance.uuid)}",
            "lang": "ru",
            "params": {
                "user_id": self.instance.club_user.user.outer_payer_id,
                "flag_get_url": 1,
                "pay_token_flag": 1,
                "verification_flag": 0,
            }
        }))

    def finalize_response(self, response):
        if response and response.get('success') and response.get('data'):
            resp_data = b64_decode(response['data'])
            # print(resp_data)
            return resp_data['url']


class OVRecurrentPaymentService(BaseOneVisionService):
    """Оплата сохраненной картой"""

    endpoint = "/pay/recurrent"
    method = "POST"
    save_serializer = None
    instance: 'Booking'

    def run_service(self):
        return self.fetch(data=self.form_encoded_data({
            "api_key": settings.ONE_VISION_API_KEY,
            "expiration": date_format(self.instance.expiration_date),
            "amount": str(self.instance.amount),
            "currency": "KZT",
            "description": "Оплата брони",
            "reference": str(self.instance.uuid),
            "success_url": "http://127.0.0.1:8008/admin",
            "failure_url": "http://127.0.0.1:8008/admin",
            "lang": "ru",
            "pay_token": self.instance.payment_card.pay_token,
            "params": {
                "user_id": self.instance.club_user.user.outer_payer_id,
                "flag_get_url": 1,
                "pay_token_flag": 1,
                "verification_flag": 0,
            }
        }))

    def finalize_response(self, response):
        if response and response.get('success') and response.get('data'):
            resp_data = b64_decode(response['data'])
            print(resp_data)
            handle_ov_response(resp_data, is_webhook=False)
            return PAYMENT_STATUSES_MAPPER.get(resp_data['status']), resp_data['processing_error_msg']
