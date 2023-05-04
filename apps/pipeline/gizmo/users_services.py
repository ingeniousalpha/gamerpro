import logging
from typing import Any

from apps.clubs.models import ClubBranchUser
from apps.pipeline.gizmo.base import BaseGizmoService
from apps.pipeline.gizmo.serializers import GizmoUsersSaveSerializer


class GizmoGetUsersService(BaseGizmoService):
    endpoint = "/api/users"
    save_serializer = GizmoUsersSaveSerializer
    method = "GET"

    def run_service(self) -> Any:
        return self.fetch()

    def get_correct_phone(self, *args):
        correct_phone = ""
        for phone in args:
            if phone and phone.startswith('+7') and len(phone) == 12:
                correct_phone = phone

            if phone and phone.startswith('8') and len(phone) == 11:
                correct_phone = "+7" + phone[1:]

        return correct_phone

    def finalize_response(self, response):
        if response.get('result') and isinstance(response['result'], list):
            resp_data = response['result']
            for gizmo_user in resp_data:
                if not ClubBranchUser.objects.filter(
                        gizmo_id=gizmo_user['id'],
                        club_branch_id=self.instance.id
                ).exists():
                    serializer = self.save_serializer(
                        data={
                            "gizmo_id": gizmo_user['id'],
                            "gizmo_phone": self.get_correct_phone(gizmo_user['phone'], gizmo_user['mobilePhone']),
                            "login": gizmo_user['username'],
                            "club_branch": self.instance.id
                        }
                    )
                    try:
                        serializer.is_valid(raise_exception=True)
                        serializer.save()
                    except Exception as e:
                        self.log_error(e)
