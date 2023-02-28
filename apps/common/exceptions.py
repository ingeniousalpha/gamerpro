from constance import config
from django.conf import settings
from rest_framework.exceptions import APIException

from config.constants.error_codes import EMAIL_CONFIRMATION_EXPIRED, EMAIL_ALREADY_CONFIRMED


class BaseAPIException(APIException):

    def get_message(self, lang=settings.DEFAULT_LANGUAGE):
        error_code = f"{self.default_code}_{lang}"
        return getattr(config, error_code)


class EmailConfirmationExpired(BaseAPIException):
    status_code = 400
    default_code = EMAIL_CONFIRMATION_EXPIRED


class EmailAlreadyConfirmed(BaseAPIException):
    status = 400
    default_code = EMAIL_ALREADY_CONFIRMED
