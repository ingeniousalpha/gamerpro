import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from django.core.exceptions import ValidationError
from django.conf import settings
from phonenumber_field.phonenumber import PhoneNumber
from pip._vendor import requests
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer as BaseTokenObtainPairSerializer
from constance import config

from apps.common.exceptions import BaseAPIException
from apps.users.exceptions import PasswordMinLength, PasswordsAreNotEqual, PasswordInvalid
from .exceptions import InvalidOTP
from .models import OTP

logger_users = logging.getLogger("users")


def validate_password(password1, password2=None):
    """ Проверка пароля при регистрации """

    if password2:
        if password1 != password2:
            raise PasswordsAreNotEqual
    if len(password1) < 8:
        raise PasswordMinLength
    elif password1.isalpha():
        raise PasswordInvalid
    elif password1 == password1.lower():
        raise PasswordInvalid
    elif password1 == password1.upper():
        raise PasswordInvalid

    return None


def is_valid_password(password):
    if len(password) < 8 or password.isalpha() \
            or password == password.lower() or password == password.lower():
        return False
    return True


def validate_password_in_forms(password1, password2=None):
    try:
        validate_password(password1, password2)
    except BaseAPIException as e:
        ValidationError(e.get_message())


def verify_otp(code: str, mobile_phone: PhoneNumber, save=False):
    otp = OTP.objects.active().filter(mobile_phone=str(mobile_phone)).last()

    if config.USE_DEFAULT_OTP and code == config.DEFAULT_OTP:
        return True
    elif not otp or otp.code != code:
        raise InvalidOTP

    if save:
        otp.verified = True
        otp.save(update_fields=["verified"])

    return True


def tg_auth_send_otp_code(mobile_phone: str):
    resp = requests.post(
        url=settings.TG_AUTH_BOT_HOST,
        json={"phoneNumber": mobile_phone}
    )
    logger_users.info(f"tg_auth_send_otp_code: {resp}")
    logger_users.info(str(resp.request.body))
    if resp.status_code == 201:
        return True
    return False


def tg_auth_verify(mobile_phone: str, otp_code):
    resp = requests.post(
        url=settings.TG_AUTH_BOT_HOST + '/verify',
        json={"phoneNumber": mobile_phone, "code": otp_code}
    )
    logger_users.info(f"tg_auth_verify: {resp}")
    logger_users.info(str(resp.request.body))
    if resp.json() == True:
        return True
    return False


# def validate_email(email):
#     """ Проверка почты при регистрации """
#
#     email = email.lower()
#     message = get_msg_by_language(MSG_ENTER_CORRECT_EMAIL, lang)
#     message_user_exists = get_msg_by_language(MSG_SUCH_USER_EXISTS, lang)
#
#     # Проверка на корректность почты
#     if '@' not in email or email[0] == '@':
#         return message
#
#     wdl = email.split('.')  # without dots list
#     if len(wdl[-1]) < 2:
#         return message
#
#     for i in wdl:
#         if i == '':
#             return message
#         if i.endswith('@') or i.startswith('@'):
#             return message
#
#     index = email.index('@')
#     after_a = email[index+1:]
#     if not after_a.replace('.', '').isalnum():
#         return message
#
#     after_a = after_a.find('.')
#     if after_a < 0:
#         return message
#
#     # Проверка на наличие пользователя с такой почтой
#     exists, _ = user_exists(email, check_if_active=False)
#     if exists:
#         return message_user_exists
#
    # return None


def generate_access_and_refresh_tokens_for_user(user):
    refresh = BaseTokenObtainPairSerializer.get_token(user)
    return {
        "refresh_token": str(refresh),
        "access_token": str(refresh.access_token),
    }


def send_email_verification_otp(recipient_email):
    sender_email = config.EMAIL_OTP_SENDER
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = config.EMAIL_OTP_SUBJECT
    msg.attach(MIMEText(f'Код подтверждения: 1111'))
    try:
        server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT)
        server.ehlo()
        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.close()
        logger_users.info(f'Sending otp to {recipient_email} succeed')
    except Exception as e:
        logger_users.info(f'Sending otp to {recipient_email} failed')
        logger_users.exception(e)
