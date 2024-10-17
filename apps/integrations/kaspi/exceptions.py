from apps.common.exceptions import BaseAPIException
from config.constants.error_codes import KASPI_SERVICE_ERROR


class KaspiServiceError(BaseAPIException):
    status_code = 400
    default_code = KASPI_SERVICE_ERROR
