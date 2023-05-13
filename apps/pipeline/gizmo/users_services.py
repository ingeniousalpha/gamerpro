from django.contrib.auth import get_user_model

from apps.authentication.exceptions import UserNotFound
from apps.clubs.models import ClubBranchUser
from apps.clubs.services import get_correct_phone
from apps.pipeline.gizmo.base import BaseGizmoService
from apps.pipeline.gizmo.exceptions import UserDoesNotHavePhoneNumber
from apps.pipeline.gizmo.serializers import GizmoUserSaveSerializer

User = get_user_model()


class GizmoGetUsersService(BaseGizmoService):
    endpoint = "/api/users"
    save_serializer = GizmoUserSaveSerializer
    method = "GET"

    def save(self, response):
        if response.get('result') and isinstance(response['result'], list):
            resp_data = response['result']
            for gizmo_user in resp_data:
                if not ClubBranchUser.objects.filter(
                        gizmo_id=gizmo_user['id'],
                        club_branch_id=self.instance.id
                ).exists():
                    try:
                        gizmo_phone = get_correct_phone(gizmo_user['phone'], gizmo_user['mobilePhone'])
                        if gizmo_phone:
                            serializer = self.save_serializer(
                                data={
                                    "gizmo_id": gizmo_user['id'],
                                    "gizmo_phone": gizmo_phone,
                                    "login": gizmo_user['username'],
                                    "club_branch": self.instance.id
                                }
                            )
                            serializer.is_valid(raise_exception=True)
                            serializer.save()
                    except Exception as e:
                        self.log_error(e)


class GizmoGetUserByUsernameService(BaseGizmoService):
    endpoint = "/api/users/{username}/username"
    save_serializer = None
    method = "GET"

    def run_service(self):
        print("self.kwargs.get('username'): ", self.kwargs.get('username'))
        return self.fetch(path_params={
            "username": self.kwargs.get('username')
        })

    def finalize_response(self, response):
        print(response)
        gizmo_user = response.get('result')
        if not gizmo_user:
            raise UserNotFound

        gizmo_phone = get_correct_phone(gizmo_user['phone'], gizmo_user['mobilePhone'])
        if not gizmo_phone:
            raise UserDoesNotHavePhoneNumber

        try:
            user = User.objects.filter(mobile_phone=gizmo_phone).first()
            if user:
                user = user.id
            serializer = GizmoUserSaveSerializer(
                data={
                    "gizmo_id": gizmo_user['id'],
                    "gizmo_phone": gizmo_phone,
                    "login": gizmo_user['username'],
                    "club_branch": self.instance.id,
                    "user": user
                }
            )
            serializer.is_valid(raise_exception=True)
            club_user = serializer.save()
            return club_user

        except Exception as e:
            self.log_error(e)
