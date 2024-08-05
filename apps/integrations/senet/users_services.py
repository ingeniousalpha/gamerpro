from typing import Any

from apps.clubs.models import ClubBranchUser
from apps.clubs.services import get_correct_phone
from apps.integrations.senet.base import BaseSenetService
from apps.integrations.soft_serializers import OuterUserSaveSerializer


class SenetGetUsersService(BaseSenetService):
    endpoint = "/api/v2/account/?limit=500&offset={offset}"
    save_serializer = OuterUserSaveSerializer
    method = "GET"

    def run_request(self):
        return self.fetch(path_params={
            "offset": self.kwargs.get('offset', 0)
        })

    def save(self, response):
        resp_data = response['results']

        if self.kwargs.get('offset', 0) > 0:
            return

        while response.get('next'):
            offset = self.kwargs.get('offset', 0) + 500
            response = SenetGetUsersService(instance=self.instance, offset=offset).run()
            resp_data += response['results']

        existed_ids = list(ClubBranchUser.objects.filter(club_branch=self.instance).values_list('outer_id', flat=True))
        non_existent_users = list(filter(lambda i: i['account_id'] not in existed_ids, resp_data))

        for outer_user in non_existent_users:
            try:
                outer_phone = get_correct_phone(outer_user['dic_user']['phone'])
                serializer = self.save_serializer(
                    data={
                        "outer_id": outer_user['account_id'],
                        "outer_phone": outer_phone,
                        "login": outer_user['dic_user']['login'],
                        "first_name": outer_user['dic_user']['name'],
                        "club_branch": self.instance.id
                    }
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()
            except Exception as e:
                self.log_error(e)
