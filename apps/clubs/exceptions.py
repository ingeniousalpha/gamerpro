from apps.common.exceptions import BaseAPIException
from config.constants.error_codes import CLUB_BRANCH_NOT_FOUND


class ClubBranchNotFound(BaseAPIException):
    status_code = 400
    default_code = CLUB_BRANCH_NOT_FOUND
