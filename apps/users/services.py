from uuid import uuid4

from apps.authentication.exceptions import UserNotFound, UserAlreadyExists
from apps.integrations.senet.users_services import SenetSearchUserService
from apps.users.models import User


def generate_mock_email():
    random_string = str(uuid4())[:8]
    return f"{random_string}@gp.com"


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

    user = User.objects.create(mobile_phone=mobile_phone, email=generate_mock_email())
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


def get_senet_user_balance(club_branch_user):
    response = SenetSearchUserService(
        instance=club_branch_user.club_branch,
        phone_number=club_branch_user.user.mobile_phone_without_code
    ).run()
    for account in response:
        if club_branch_user.outer_id == account.get('account_id'):
            total_balance = int(account.get('account_amount')) + int(account.get('bonus_account_amount'))
            club_branch_user.balance = total_balance
            club_branch_user.save(update_fields=['balance'])
            return total_balance
    return 0
