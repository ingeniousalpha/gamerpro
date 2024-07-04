from decimal import Decimal

from constance import config

from .models import ClubBranchUser, ClubUserCashback


def get_correct_phone(*args):
    correct_phone = ""
    for phone in args:
        if phone and phone.startswith('+7') and len(phone) == 12:
            correct_phone = phone

        if phone and phone.startswith('8') and len(phone) == 11:
            correct_phone = "+7" + phone[1:]

        if phone and phone.startswith('7') and len(phone) == 10:
            correct_phone = "+7" + phone

        if phone and phone.startswith('7') and len(phone) == 11:
            correct_phone = "+" + phone

    return correct_phone


def get_club_branch_user_by_username(username):
    return ClubBranchUser.objects.filter(login=username).first()


def add_cashback(user, club, from_amount: Decimal = None, amount: int = None):
    amount_to_add = 0
    if from_amount:
        amount_to_add = int(from_amount * config.CASHBACK_PERCENT / 100)
    elif amount:
        amount_to_add = int(amount)

    if amount_to_add == 0:
        raise Exception("There is no amount_to_add for cashback")

    user_cb = ClubUserCashback.objects.filter(user=user, club=club).first()
    if user_cb:
        user_cb.cashback_amount += amount_to_add
        user_cb.save()
    else:
        ClubUserCashback.objects.create(
            user=user, club=club, cashback_amount=amount_to_add
        )
