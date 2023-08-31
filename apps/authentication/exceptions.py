from apps.common.exceptions import BaseAPIException
from config.constants.error_codes import USER_NOT_FOUND, USER_ALREADY_EXISTS, INVALID_OTP, \
    USER_ALREADY_HAS_ACTIVE_BOOKING


class UserNotFound(BaseAPIException):
    status_code = 400
    default_code = USER_NOT_FOUND


class UserAlreadyHasActiveBooking(BaseAPIException):
    status_code = 400
    default_code = USER_ALREADY_HAS_ACTIVE_BOOKING


class UserAlreadyExists(BaseAPIException):
    status_code = 400
    default_code = USER_ALREADY_EXISTS


class InvalidOTP(BaseAPIException):
    status_code = 400
    default_code = INVALID_OTP
