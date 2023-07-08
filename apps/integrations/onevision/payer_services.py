from django.conf import settings

from apps.common.utils import b64_decode
from apps.integrations.onevision.base import BaseOneVisionService
from apps.integrations.onevision.serializers import OVSavePayerIDSerializer


class OVCreatePayerService(BaseOneVisionService):
    endpoint = "/pay/payer_create"
    method = "POST"
    save_serializer = OVSavePayerIDSerializer
    instance: 'User'

    def run_service(self):
        return self.fetch(data=self.form_encoded_data({
            "api_key": settings.ONE_VISION_API_KEY,
            "description": str(self.instance.secret_key)
        }))

    def prepare_to_save(self, response: dict) -> dict:
        print(response)
        if response and response.get('success'):
            resp_data = b64_decode(response['data'])
            return {
                "outer_payer_id": resp_data['payer_key']
            }
        return {}
