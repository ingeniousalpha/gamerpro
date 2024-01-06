from apps.common.exceptions import BaseAPIException
from config.constants.error_codes import BOOKING_NOT_FOUND, BOOKING_STATUS_IS_NOT_APPROPRIATE, USER_NEED_TO_VERIFY_IIN


class BookingNotFound(BaseAPIException):
    status_code = 400
    default_code = BOOKING_NOT_FOUND


class BookingStatusIsNotAppropriate(BaseAPIException):
    status_code = 400
    default_code = BOOKING_STATUS_IS_NOT_APPROPRIATE


class UserNeedToVerifyIIN(BaseAPIException):
    status_code = 400
    default_code = USER_NEED_TO_VERIFY_IIN
