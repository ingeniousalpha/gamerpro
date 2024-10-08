import logging

from requests.exceptions import ConnectTimeout, ConnectionError, HTTPError, RequestException

from apps.clubs import SoftwareTypes
from apps.clubs.models import ClubBranch
from apps.integrations.gizmo.computers_services import GizmoGetComputerGroupsService, GizmoGetComputersService
from apps.integrations.gizmo.time_packets_services import GizmoGetTimePacketGroupsService, GizmoGetTimePacketsService
from apps.integrations.gizmo.users_services import GizmoGetUsersService, GizmoUpdateComputerStateByUserSessionsService
from apps.integrations.senet.computers_services import (
    SenetGetComputerZonesService, SenetGetComputersWithSessionsService
)
from apps.integrations.senet.time_packets_services import SenetGetTimePacketsService
from apps.integrations.senet.users_services import SenetGetUsersService
from config.celery_app import cel_app

logger = logging.getLogger("clubs")


@cel_app.task
def synchronize_club_branch(club_branch_id):
    club_branch = ClubBranch.objects.select_related('club').get(id=club_branch_id)
    software_type = club_branch.club.software_type
    if software_type == SoftwareTypes.GIZMO:
        GizmoGetUsersService(instance=club_branch).run()
        GizmoGetComputerGroupsService(instance=club_branch).run()
        GizmoGetTimePacketGroupsService(instance=club_branch).run()
        GizmoGetTimePacketsService(instance=club_branch).run()
        _sync_club_branch_computers(club_branch)
        return True
    elif software_type == SoftwareTypes.SENET:
        if club_branch.main_club_branch is None:
            SenetGetUsersService(instance=club_branch).run()
        else:
            logger.info(f"SENET users must be synchronized through the main club branch")
        SenetGetComputerZonesService(instance=club_branch).run()
        SenetGetTimePacketsService(instance=club_branch).run()
        _sync_club_branch_computers(club_branch)
        return True
    else:
        logger.error(f"Unknown software type: {software_type}")
        return False


@cel_app.task
def synchronize_all_computers():
    for club_branch in ClubBranch.objects.select_related('club').filter(is_active=True):
        _sync_club_branch_computers(club_branch)


def _sync_club_branch_computers(club_branch):
    software_type = club_branch.club.software_type
    try:
        if software_type == SoftwareTypes.GIZMO:
            GizmoGetComputersService(instance=club_branch).run()
            GizmoUpdateComputerStateByUserSessionsService(instance=club_branch).run()
        elif software_type == SoftwareTypes.SENET:
            SenetGetComputersWithSessionsService(instance=club_branch).run()
        if not club_branch.is_turned_on:
            club_branch.is_turned_on = True
            club_branch.save(update_fields=['is_turned_on'])
    except (ConnectTimeout, ConnectionError, HTTPError, RequestException):
        print(f'connection exception handled, branch {club_branch} turned off')
        if club_branch.is_turned_on:
            club_branch.is_turned_on = False
            club_branch.save(update_fields=['is_turned_on'])
