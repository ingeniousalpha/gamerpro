from uuid import uuid4
from django.conf import settings
from django.utils import timezone

from apps.common.services import date_format
from apps.payments.services import handle_ov_response
from apps.common.utils import b64_decode
from apps.integrations.onevision.base import BaseOneVisionService


class OVInitPaymentService(BaseOneVisionService):
    """Оплата новой картой"""

    endpoint = "/pay"
    method = "POST"
    save_serializer = None
    instance: 'Booking'

    def run_service(self):
        return self.fetch(data=self.form_encoded_data({
            "api_key": self.club_api_key,
            "expiration": date_format(self.instance.expiration_date),
            "amount": str(self.instance.total_amount),
            "currency": "KZT",
            "description": "Оплата брони",
            "reference": str(self.instance.uuid),
            "success_url": f"{settings.SITE_DOMAIN}/api/payments/success?booking_uuid={str(self.instance.uuid)}",
            # "failure_url": f"{settings.SITE_DOMAIN}/api/payments/fail?booking_uuid={str(self.instance.uuid)}",
            "lang": "ru",
            "params": {
                "user_id": self.instance.club_user.onevision_payer_id,
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
        is_repl = self.kwargs.get('is_replenishment', False)
        repl_ref = str(self.kwargs.get('replenishment_reference', ""))
        self.kwargs['reference'] = str(uuid4())

        if is_repl and repl_ref:
            self.kwargs['description'] = "REPLENISHMENT" + f"_{repl_ref}"
        elif is_repl and not repl_ref:
            self.kwargs['description'] = "REPLENISHMENT"
        else:
            self.kwargs['description'] = "Оплата сохр картой"
            self.kwargs['reference'] = str(self.instance.uuid)

        return self.fetch(data=self.form_encoded_data({
            "api_key": self.club_api_key,
            "amount": str(self.kwargs.get('total_amount', '')) or str(self.instance.total_amount),
            "expiration": date_format(timezone.now()),
            "currency": "KZT",
            "description": self.kwargs['description'],
            "reference": self.kwargs['reference'],
            "lang": "ru",
            "pay_token": self.kwargs.get('pay_token', '') or self.instance.payment_card.pay_token,
            "params": {
                "user_id": self.kwargs.get('outer_payer_id', '') or self.instance.club_user.onevision_payer_id,
                "flag_get_url": 1,
                "pay_token_flag": 1,
                "verification_flag": 0,
            }
        }))

    def finalize_response(self, response):
        resp_data = b64_decode(response.get('data'))
        # print("resp_data: ", resp_data)
        if resp_data and response.get('success'):
            resp_data['description'] = self.kwargs.get('description')
            if 'params' not in resp_data:
                resp_data['params'] = {'user_id': self.kwargs.get('outer_payer_id') or self.instance.club_user.onevision_payer_id}
            payment = handle_ov_response(resp_data, is_webhook=False)
            return payment, resp_data['processing_error_msg']
        else:
            error_msg = resp_data['error_msg']
            if resp_data.get('error_data'):
                error_msg = f"{error_msg}: {str(resp_data['error_data'])}"
            return None, error_msg
