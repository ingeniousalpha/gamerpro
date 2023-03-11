from phonenumbers import PhoneNumber

from apps.authentication.models import OTP


def send_otp(mobile_phone: PhoneNumber):
    otp = OTP.generate(mobile_phone)
    print(f'{mobile_phone=} {otp=}')
    # send_sms(otp)
