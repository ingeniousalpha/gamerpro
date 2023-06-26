from apps.common.exceptions import BaseAPIException
from config.constants.error_codes import USER_DOES_NOT_HAVE_PHONE_NUMBER, GIZMO_REQUEST_ERROR


class UserDoesNotHavePhoneNumber(BaseAPIException):
    status_code = 400
    default_code = USER_DOES_NOT_HAVE_PHONE_NUMBER


class GizmoRequestError(BaseAPIException):
    status_code = 400
    default_code = GIZMO_REQUEST_ERROR
