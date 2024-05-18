import pytz
import datetime
import logging
import string
from random import choice, randint
from django.conf import settings

from apps.common.models import HandledException

logger_users = logging.getLogger("users")


def generate_random_string(size=10):
    letters_and_digits = string.ascii_letters + string.digits
    random_code = ''.join((choice(letters_and_digits) for i in range(size)))
    return random_code


def generate_password():
    digits = [int(i) for i in string.digits]
    password = generate_random_string(10)
    password = [i for i in password]
    password[digits.pop(randint(0, len(digits)-1))] = choice(string.ascii_lowercase)
    password[digits.pop(randint(0, len(digits)-1))] = choice(string.ascii_uppercase)
    password[digits.pop(randint(0, len(digits)-1))] = choice(string.digits)

    return "".join(password)


def save_error(error_code, error_message, stack_trace=None):
    return HandledException.objects.create(
        code=error_code[:512],
        message=error_message[:512],
        stack_trace=stack_trace
    ).pk


def str_to_datetime(string_dt):
    return datetime.datetime.strptime(string_dt, '%Y-%m-%d %H:%M:%S')


def date_format(dt):
    return datetime.datetime.strftime(dt.astimezone(pytz.timezone(settings.TIME_ZONE)), '%Y-%m-%d %H:%M')


def date_format_with_t(dt):
    return datetime.datetime.strftime(dt.astimezone(), '%Y-%m-%dT%H:%M')
