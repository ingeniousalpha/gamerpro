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
                            "login": gizmo_user['username'],
                            "club_branch": self.instance
                        }
                    )
                    try:
                        serializer.is_valid(raise_exception=True)
                        serializer.save()
                    except Exception as e:
                        self.log_error(e)
