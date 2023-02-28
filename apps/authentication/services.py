import logging
from django.core.exceptions import ValidationError

from apps.common.exceptions import BaseAPIException
from apps.users.exceptions import PasswordMinLength, PasswordsAreNotEqual, PasswordInvalid

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
