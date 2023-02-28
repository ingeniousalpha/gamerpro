from apps.authentication.exceptions import UserNotFound
from apps.users.models import User


def create_user(email, password):
    user = User.objects.filter(email=email).first()

    if user and user.check_password(password):
        return user

    user = User.objects.create(email=email)
    user.set_password(password)
    user.save(update_fields=['password'])

    return user


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
