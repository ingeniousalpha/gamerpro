from apps.common.exceptions import BaseAPIException
from config.constants.error_codes import SENET_NO_ACTIVE_CASHBOX, SENET_INVALID_CASHBOX_CREDENTIALS, SENET_INTEGRATION_ERROR


class SenetNoActiveCashbox(BaseAPIException):
    status_code = 400
    default_code = SENET_NO_ACTIVE_CASHBOX


class SenetInvalidCashboxCredentials(BaseAPIException):
    status_code = 400
    default_code = SENET_INVALID_CASHBOX_CREDENTIALS


class SenetIntegrationError(BaseAPIException):
    status_code = 400
    default_code = SENET_INTEGRATION_ERROR
