import hmac
import logging
import os

from apps.integrations.kaspi.exceptions import KaspiServiceInputDataInvalid
from apps.integrations.services import BaseService
from apps.integrations.services.base import ServiceLoggingMixin

logger = logging.getLogger("kaspi")


class BaseKaspiService(ServiceLoggingMixin, BaseService):
    headers = {
        "Content-Type": "application/json",
    }
    # instance = Payment
    host = "https://kaspi.kz"

    def __init__(self, instance=None, **kwargs):
        super().__init__(instance, **kwargs)

        if not kwargs.get('club_branch'):
            raise KaspiServiceInputDataInvalid

        trader_code = kwargs['club_branch'].trader.code.upper()

        club_api_key = os.getenv(f"ONE_VISION_{trader_code}_API_KEY")
        club_api_secret_key = os.getenv(f"ONE_VISION_{trader_code}_API_SECRET_KEY")
        if not club_api_key or not club_api_secret_key:
            raise KaspiServiceInputDataInvalid

        self.club_api_key = club_api_key
        self.club_api_secret_key = club_api_secret_key

    def log_error(self, e):
        logger.info(f"{self.__class__.__name__} Error: {e}")
