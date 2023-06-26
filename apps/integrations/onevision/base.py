import base64
import hmac
import json
import logging
import uuid

from django.conf import settings
from django.utils import timezone

from apps.payments.services import b64_encode, b64_decode
from apps.integrations.services import BaseService
from apps.integrations.services.base import ServiceLoggingMixin

logger = logging.getLogger("onevision")


class BaseOneVisionService(ServiceLoggingMixin, BaseService):
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }
    # instance = Payment
    host = "https://1vision.app"

    def log_error(self, e):
        logger.info(f"{self.__class__.__name__} Error: {e}")

    def form_sign(self, data):
        return hmac.new(
            settings.ONE_VISION_API_SECRET_KEY.encode('ascii'),
            data.encode('ascii'),
            'MD5'
        ).hexdigest()

    def form_encoded_data(self, raw_data):
        print(raw_data)
        raw_data_base64 = b64_encode(raw_data)
        return {
            "data": raw_data_base64,
            "sign": self.form_sign(raw_data_base64)
        }
