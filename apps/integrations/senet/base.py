import logging
from abc import abstractmethod
from typing import Any

from django.core.cache import cache

from apps.clubs.models import ClubBranch
from apps.integrations.exceptions import UnauthorizedError
from apps.integrations.services import BaseService
from apps.integrations.services.base import ServiceLoggingMixin

logger = logging.getLogger("senet")


class BaseSenetService(ServiceLoggingMixin, BaseService):
    headers = {
        "Content-Type": "application/json",
    }
    instance: ClubBranch

    def __init__(self, instance=None, **kwargs):
        super().__init__(instance, **kwargs)
        self.headers["Authorization"] = f'Token {self.get_auth_token()}'

    def get_url(self, path_params) -> str:
        self.host = self.instance.api_host
        return super().get_url(path_params)

    def get_auth_token(self):
        senet_token = cache.get(f"SENET_AUTH_TOKEN_{self.instance.id}")
        if senet_token:
            return senet_token

        return self.set_new_auth_token()

    def set_new_auth_token(self):
        senet_token = GetSenetAuthTokenService(instance=self.instance).run()
        cache.set(f"SENET_AUTH_TOKEN_{self.instance.id}", senet_token, timeout=24*60*60)
        return senet_token

    @abstractmethod
    def run_request(self) -> Any:
        """
        This method should be overload
        """

    def run_service(self):
        try:
            return self.run_request()
        except UnauthorizedError:
            self.headers["Authorization"] = f'Token {self.set_new_auth_token()}'
            return self.run_request()
        except Exception as e:
            raise e

    def log_error(self, e):
        logger.info(f"{self.__class__.__name__} Error: {e}")


class BaseSenetCashboxService(BaseSenetService):

    def get_auth_token(self):
        senet_token = cache.get(f"SENET_CASHBOX_AUTH_TOKEN_{self.instance.id}")
        return senet_token if senet_token else self.set_new_auth_token()

    def set_new_auth_token(self):
        senet_token = GetSenetAuthTokenService(instance=self.instance, is_cashbox=True).run()
        cache.set(f"SENET_CASHBOX_AUTH_TOKEN_{self.instance.id}", senet_token, timeout=24*60*60)
        return senet_token


class GetSenetAuthTokenService(ServiceLoggingMixin, BaseService):
    endpoint = "/api/v2/user/admin_auth/"
    instance: ClubBranch

    def get_url(self, path_params) -> str:
        self.host = self.instance.api_host
        return super().get_url(path_params)

    def run_service(self):
        if self.kwargs and self.kwargs.get('is_cashbox'):
            username = self.instance.cashbox_user
            password = self.instance.cashbox_password
        else:
            username = self.instance.api_user
            password = self.instance.api_password
        return self.fetch(json={
            "username": username,
            "password": password,
            "grant_type": "password",
            "client_id": "test"
        })

    def finalize_response(self, response):
        token = response.get('token')
        if not token:
            logger.error(str(response))
        return token
