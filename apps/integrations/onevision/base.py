import base64
import hmac
import json
import logging
import os
import uuid

from django.conf import settings
from django.utils import timezone

from apps.common.utils import b64_encode, b64_decode
from apps.integrations.onevision.exceptions import OneVisionServiceInputDataInvalid
from apps.integrations.services import BaseService
from apps.integrations.services.base import ServiceLoggingMixin

logger = logging.getLogger("onevision")


class BaseOneVisionService(ServiceLoggingMixin, BaseService):
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }
    # instance = Payment
    host = "https://1vision.app"
    club_api_key: str = None
    club_api_secret_key: str = None

    def __init__(self, instance=None, **kwargs):
        super().__init__(instance, **kwargs)

        if not kwargs.get('club_branch'):
            raise OneVisionServiceInputDataInvalid

        trader_code = kwargs['club_branch'].trader.code.upper()

        club_api_key = os.getenv(f"ONE_VISION_{trader_code}_API_KEY")
        club_api_secret_key = os.getenv(f"ONE_VISION_{trader_code}_API_SECRET_KEY")
        if not club_api_key or not club_api_secret_key:
            raise OneVisionServiceInputDataInvalid

        self.club_api_key = club_api_key
        self.club_api_secret_key = club_api_secret_key

    def log_error(self, e):
        logger.info(f"{self.__class__.__name__} Error: {e}")

    def form_sign(self, data):
        return hmac.new(
            self.club_api_secret_key.encode('ascii'),
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
