import logging

from apps.integrations.services import BaseService
from apps.integrations.services.base import ServiceLoggingMixin

logger = logging.getLogger("kaspi")


class BaseKaspiService(ServiceLoggingMixin, BaseService):
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "server.gamerpro.kz",
        "Host": "kaspi.kz"
    }
    # instance = Payment
    host = "https://kaspi.kz"

    def log_error(self, e):
        logger.info(f"{self.__class__.__name__} Error: {e}")
