from apps.common.exceptions import BaseAPIException
from config.constants.error_codes import ONEVISION_SERVICE_INPUT_DATA_INVALID


class OneVisionServiceInputDataInvalid(BaseAPIException):
    status_code = 400
    default_code = ONEVISION_SERVICE_INPUT_DATA_INVALID

