from apps.clubs.models import ClubComputer, ClubComputerGroup
from apps.integrations.gizmo.base import BaseGizmoService
from apps.integrations.gizmo.exceptions import GizmoRequestError
from apps.integrations.gizmo.serializers import GizmoComputersSaveSerializer
from apps.integrations.soft_serializers import OuterComputerGroupsSaveSerializer


class GizmoGetComputerGroupsService(BaseGizmoService):
    endpoint = "/api/hostgroups"
    save_serializer = OuterComputerGroupsSaveSerializer
    method = "GET"

    def save(self, response):
        if response.get('result') and isinstance(response['result'], list):
            resp_data = response['result']
            for gizmo_comp_group in resp_data:
                if not ClubComputerGroup.objects.filter(
                    outer_id=gizmo_comp_group['id'],
                    club_branch_id=self.instance.id
                ).exists():
                    try:
                        serializer = self.save_serializer(
                            data={
                                "outer_id": gizmo_comp_group['id'],
                                "name": gizmo_comp_group['name'],
                                "club_branch": self.instance.id,
                            }
                        )
                        serializer.is_valid(raise_exception=True)
                        serializer.save()
                    except Exception as e:
                        self.log_error(e)


class GizmoGetComputersService(BaseGizmoService):
    endpoint = "/api/hostcomputers"
    save_serializer = GizmoComputersSaveSerializer
    method = "GET"

    def save(self, response):
        # print(response.get('result'))
        if response and response.get('result') and isinstance(response['result'], list):
            resp_data = response['result']
            for gizmo_computer in resp_data:
                if gizmo_computer['isDeleted']:
                    continue
                computer = ClubComputer.objects.filter(
                    gizmo_id=gizmo_computer['id'],
                    club_branch_id=self.instance.id
                ).first()
                if computer is None:
                    group_id = None
                    if group := ClubComputerGroup.objects.filter(
                            outer_id=gizmo_computer['hostGroupId'],
                            club_branch_id=self.instance.id
                    ).first():
                        group_id = group.id
                    serializer = self.save_serializer(
                        data={
                            "gizmo_id": gizmo_computer['id'],
                            "number": gizmo_computer['number'],
                            "gizmo_hostname": gizmo_computer['hostname'],
                            "club_branch": self.instance.id,
                            "is_locked": bool(gizmo_computer['state'] == 2),
                            "is_broken": bool(gizmo_computer['state'] in [1, 3]),
                            "group": group_id,
                        }
                    )
                    try:
                        serializer.is_valid(raise_exception=True)
                        serializer.save()
                    except Exception as e:
                        self.log_error(e)
                else:
                    computer.is_locked = bool(gizmo_computer['state'] == 2)
                    computer.is_broken = bool(gizmo_computer['state'] in [1, 3])
                    computer.number = gizmo_computer['number']
                    computer.gizmo_hostname = gizmo_computer['hostname']
                    computer.save(update_fields=['is_locked', 'is_broken', 'number', 'gizmo_hostname'])


class GizmoLockComputerService(BaseGizmoService):
    endpoint = "/api/hosts/{computer_id}/lock/true"
    save_serializer = None
    method = "POST"

    def run_service(self):
        return self.fetch(path_params={
            "computer_id": self.kwargs.get('computer_id')
        })

    def finalize_response(self, response):
        if response.get('isError') == True:
            self.log_error(str(response))
            raise GizmoRequestError


class GizmoUnlockComputerService(BaseGizmoService):
    endpoint = "/api/hosts/{computer_id}/lock/false"
    save_serializer = None
    method = "POST"

    def run_service(self):
        return self.fetch(path_params={
            "computer_id": self.kwargs.get('computer_id')
        })

    def finalize_response(self, response):
        if response.get('isError') == True:
            self.log_error(str(response))
            raise GizmoRequestError
