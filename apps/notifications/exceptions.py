from apps.common.exceptions import BaseAPIException
from config.constants.error_codes import ACCESS_DENIED


class RetryTaskException(Exception):
    pass

class AccessDenied(BaseAPIException):
    status_code = 403
    default_code = ACCESS_DENIED
