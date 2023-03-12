from constance import config
from django.conf import settings
from rest_framework.exceptions import APIException

from config.constants.error_codes import EMAIL_CONFIRMATION_EXPIRED, EMAIL_ALREADY_CONFIRMED, INVALID_INPUT_DATA


class BaseAPIException(APIException):

    def get_message(self):
        return getattr(config, self.default_code)


class EmailConfirmationExpired(BaseAPIException):
    status_code = 400
    default_code = EMAIL_CONFIRMATION_EXPIRED


class EmailAlreadyConfirmed(BaseAPIException):
    status_code = 400
    default_code = EMAIL_ALREADY_CONFIRMED


class InvalidInputData(BaseAPIException):
    status_code = 400
    default_code = INVALID_INPUT_DATA
