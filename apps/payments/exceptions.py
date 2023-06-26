from apps.common.exceptions import BaseAPIException


class OVRecurrentPaymentFailed(BaseAPIException):
    status_code = 400
    default_code = "ov_recurrent_payment_failed"
