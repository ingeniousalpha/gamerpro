from apps.common.exceptions import BaseAPIException
from config.constants.error_codes import SENET_NO_ACTIVE_CASHBOX, SENET_INVALID_CASHBOX_CREDENTIALS


class SenetNoActiveCashbox(BaseAPIException):
    status_code = 400
    default_code = SENET_NO_ACTIVE_CASHBOX


class SenetInvalidCashboxCredentials(BaseAPIException):
    status_code = 400
    default_code = SENET_INVALID_CASHBOX_CREDENTIALS
