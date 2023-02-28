from apps.common.exceptions import BaseAPIException
from config.constants.error_codes import USER_NOT_FOUND, USER_ALREADY_EXISTS


class UserNotFound(BaseAPIException):
    status_code = 400
    default_code = USER_NOT_FOUND


class UserAlreadyExists(BaseAPIException):
    status_code = 400
    default_code = USER_ALREADY_EXISTS
