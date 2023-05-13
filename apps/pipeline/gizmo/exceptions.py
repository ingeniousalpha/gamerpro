from apps.common.exceptions import BaseAPIException
from config.constants.error_codes import USER_DOES_NOT_HAVE_PHONE_NUMBER


class UserDoesNotHavePhoneNumber(BaseAPIException):
    status_code = 400
    default_code = USER_DOES_NOT_HAVE_PHONE_NUMBER
