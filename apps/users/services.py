from apps.authentication.exceptions import UserNotFound, UserAlreadyExists
from apps.users.models import User


def create_user(email, password):
    user = User.objects.filter(email=email).first()

    if user and user.check_password(password):
        return user

    user = User.objects.create(email=email)
    user.set_password(password)
    user.save(update_fields=['password'])

    return user


def get_or_create_user_by_phone(mobile_phone, raise_exception=False):
    """Returns True if created, else False"""

    user = User.objects.filter(mobile_phone=str(mobile_phone)).first()

    if user:
        if raise_exception:
            raise UserAlreadyExists
        return user, False

    user = User.objects.create(mobile_phone=mobile_phone)
    return user, True


def get_user(email):
    """ Проверка существует ли пользователь """

    user = User.objects.active().filter(email=email).first()

    if user and user.get_is_active():
        return user


def get_user_by_login(email, password, raise_exception=False):
    user = get_user(email)

    if user and user.check_password(password):
        return user

    if raise_exception:
        raise UserNotFound
