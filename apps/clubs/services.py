from apps.clubs.models import ClubBranchUser


def get_correct_phone(*args):
    correct_phone = ""
    for phone in args:
        if phone and phone.startswith('+7') and len(phone) == 12:
            correct_phone = phone

        if phone and phone.startswith('8') and len(phone) == 11:
            correct_phone = "+7" + phone[1:]

        if phone and phone.startswith('7') and len(phone) == 10:
            correct_phone = "+7" + phone

    return correct_phone


def get_club_branch_user_by_username(username):
    return ClubBranchUser.objects.filter(login=username).first()
