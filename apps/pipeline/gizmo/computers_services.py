from typing import Any

from apps.clubs.models import ClubComputer, ClubComputerGroup
from apps.pipeline.gizmo.base import BaseGizmoService
from apps.pipeline.gizmo.serializers import GizmoComputersSaveSerializer, GizmoComputerGroupsSaveSerializer


class GizmoGetComputerGroupsService(BaseGizmoService):
    endpoint = "/api/hostgroups"
    save_serializer = GizmoComputerGroupsSaveSerializer
    method = "GET"

    def save(self, response):
        if response.get('result') and isinstance(response['result'], list):
            resp_data = response['result']
            for gizmo_comp_group in resp_data:
                if not ClubComputerGroup.objects.filter(
                    gizmo_id=gizmo_comp_group['id'],
                    club_branch_id=self.instance.id
                ).exists():
                    try:
                        serializer = self.save_serializer(
                            data={
                                "gizmo_id": gizmo_comp_group['id'],
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

    def get_booking_state(self, state: int) -> bool:
        return True if state == 2 else False

    def save(self, response):
        print(response.get('result'))
        if response.get('result') and isinstance(response['result'], list):
            resp_data = response['result']
            for gizmo_computer in resp_data:
                computer = ClubComputer.objects.filter(
                    gizmo_id=gizmo_computer['id'],
                    club_branch_id=self.instance.id
                ).first()
                if computer is None:
                    group_id = None
                    if group := ClubComputerGroup.objects.filter(gizmo_id=gizmo_computer['hostGroupId']).first():
                        group_id = group.id
                    serializer = self.save_serializer(
                        data={
                            "gizmo_id": gizmo_computer['id'],
                            "number": gizmo_computer['number'],
                            "gizmo_hostname": gizmo_computer['hostname'],
                            "club_branch": self.instance.id,
                            "is_booked": self.get_booking_state(gizmo_computer['state']),
                            "group": group_id,
                        }
                    )
                    try:
                        serializer.is_valid(raise_exception=True)
                        serializer.save()
                    except Exception as e:
                        self.log_error(e)
                else:
                    computer.is_booked = self.get_booking_state(gizmo_computer['state'])
                    computer.save()