from urllib3.exceptions import ConnectTimeoutError

from apps.clubs.models import ClubBranch
from apps.integrations.gizmo.computers_services import GizmoGetComputerGroupsService, GizmoGetComputersService
from apps.integrations.gizmo.time_packets_services import GizmoGetTimePacketGroupsService, GizmoGetTimePacketsService
from apps.integrations.gizmo.users_services import GizmoGetUsersService, GizmoUpdateComputerStateByUserSessionsService
from config.celery_app import cel_app


@cel_app.task
def synchronize_gizmo_club_branch(club_branch_id):
    club_branch = ClubBranch.objects.get(id=club_branch_id)
    GizmoGetUsersService(instance=club_branch).run()
    GizmoGetComputerGroupsService(instance=club_branch).run()
    GizmoGetTimePacketGroupsService(instance=club_branch).run()
    GizmoGetTimePacketsService(instance=club_branch).run()
    _sync_gizmo_computers_state_of_club_branch(club_branch)


@cel_app.task
def synchronize_gizmo_computers_state():
    for club_branch in ClubBranch.objects.filter(is_active=True):
        _sync_gizmo_computers_state_of_club_branch(club_branch)


def _sync_gizmo_computers_state_of_club_branch(club_branch):
    try:
        GizmoGetComputersService(instance=club_branch).run()
        GizmoUpdateComputerStateByUserSessionsService(instance=club_branch).run()
    except ConnectTimeoutError:
        club_branch.is_active = False
        club_branch.save(update_fields=['is_active'])
