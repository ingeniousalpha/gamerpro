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
        users_for_save = []

        for outer_user in non_existent_users:
            outer_phone = get_correct_phone(outer_user['dic_user']['phone'])
            users_for_save.append({
                "outer_id": outer_user['account_id'],
                "outer_phone": outer_phone,
                "login": outer_user['dic_user']['login'],
                "first_name": outer_user['dic_user']['name'],
                "club_branch": self.instance.id
            })

        try:
            serializer = self.save_serializer(data=users_for_save, many=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
        except Exception as e:
            self.log_error(e)


class SenetSearchUserByPhoneService(BaseSenetService):
    """
    This endpoint searches user by login, phone, email, name in Senet base
    But for our app at the moment we will search by phone only
    """
    endpoint = "/api/v2/account/?limit=20&search={phone}"
    save_serializer = OuterUserSaveSerializer
    method = "GET"

    def __init__(self, instance=None, **kwargs):
        super().__init__(instance, kwargs)
        self.user_found = None

    def run_request(self):
        return self.fetch(path_params={
            "search": self.kwargs.get("phone")[-10:]
        })

    def save(self, response):
        if len(response["results"]) == 0:
            return

        new_user = None
        for r in response["results"]:
            if new_user["dic_user"]["phone"][-10:] == self.kwargs.get("phone"):
                new_user = r
                break

        if not new_user:
            return

        outer_phone = get_correct_phone(new_user["dic_user"]["phone"])
        club_user = ClubBranchUser.objects.filter(
            club_branch=self.instance,
            login=new_user['dic_user']['login'],
            outer_phone=outer_phone
        ).first()

        if club_user:
            self.user_found = club_user
            return

        try:
            serializer = self.save_serializer(
                data={
                    "outer_id": new_user['account_id'],
                    "outer_phone": outer_phone,
                    "login": new_user['dic_user']['login'],
                    "first_name": new_user['dic_user']['name'],
                    "club_branch": self.instance.id
                }
            )
            serializer.is_valid(raise_exception=True)
            self.user_found = serializer.save()
        except Exception as e:
            self.log_error(e)

    def finalize_response(self, response):
        return self.user_found
