from apps.common.exceptions import BaseAPIException
from config.constants.error_codes import CLUB_BRANCH_NOT_FOUND, COMPUTER_DOES_NOT_BELONG_TO_CLUB_BRANCH, \
    COMPUTER_IS_ALREADY_BOOKED, NEED_TO_INPUT_USER_LOGIN


class ClubBranchNotFound(BaseAPIException):
    status_code = 400
    default_code = CLUB_BRANCH_NOT_FOUND


class ComputerDoesNotBelongToClubBranch(BaseAPIException):
    status_code = 400
    default_code = COMPUTER_DOES_NOT_BELONG_TO_CLUB_BRANCH


class ComputerIsAlreadyBooked(BaseAPIException):
    status_code = 400
    default_code = COMPUTER_IS_ALREADY_BOOKED


class NeedToInputUserLogin(BaseAPIException):
    status_code = 400
    default_code = NEED_TO_INPUT_USER_LOGIN
