from apps.clubs.models import ClubBranchUser
from apps.clubs.services import get_correct_phone
from apps.integrations.senet.base import BaseSenetService
from apps.integrations.senet.exceptions import SenetIntegrationError
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
        if self.kwargs.get('offset') is not None:
            return
        offset = 0
        resp_data = response['results']
        while response.get('next'):
            offset = offset + 500
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


class SenetSearchUserService(BaseSenetService):
    endpoint = "/api/v2/account/?limit=1&search={phone_number}"
    method = "GET"
    save_serializer = None

    def run_request(self):
        return self.fetch(path_params={"phone_number": self.kwargs.get("phone_number")})

    def finalize_response(self, response):
        print(f"SenetSearchUserService response_count: {response['count']}")
        if response['count'] == 0:
            raise SenetIntegrationError('Аккаунт не найден.')
        limit = 10
        max_count = limit if response['count'] > limit else response['count']
        print(f"SenetSearchUserService max_count: {max_count}")
        print(f"SenetSearchUserService full response: {response['results']}")
        print(f"SenetSearchUserService short response: {response['results'][:max_count]}")
        return response['results'][:max_count]


class SenetCreateUserService(BaseSenetService):
    endpoint = "/api/v2/account/"
    method = "POST"
    save_serializer = None

    def run_request(self):
        return self.fetch(json={
            "account_type": 1,
            "dic_user": {
                "login": self.kwargs["username"],
                "password": self.kwargs["password"],
                "phone": self.kwargs["mobile_phone"],
                "email": self.kwargs["email"]
            }
        })

    def finalize_response(self, response):
        if response.get('code') == -2:
            if response['dic_user'].get('login'):
                error_msg = "Пользователь с указанным username уже существует"
            elif response['dic_user'].get('password'):
                error_msg = "Пароль не соответствует требованиям"
            else:
                error_msg = "Непредвиденная ошибка, обратитесь в службу поддержки"
            self.log_error(error_msg)
            self.log_error(str(response))
            raise SenetIntegrationError(error_msg)
        return response
