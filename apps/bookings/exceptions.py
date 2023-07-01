from apps.common.exceptions import BaseAPIException
from config.constants.error_codes import BOOKING_NOT_FOUND


class BookingNotFound(BaseAPIException):
    status_code = 400
    default_code = BOOKING_NOT_FOUND
