from apps.clubs.models import ClubBranch
from apps.pipeline.gizmo.computers_services import GizmoGetComputerGroupsService, GizmoGetComputersService
from apps.pipeline.gizmo.users_services import GizmoGetUsersService
from config.celery_app import cel_app


@cel_app.task
def synchronize_gizmo_club_branch(club_branch_id):
    club_branch = ClubBranch.objects.get(id=club_branch_id)
    GizmoGetUsersService(instance=club_branch).run()
    GizmoGetComputerGroupsService(instance=club_branch).run()
    GizmoGetComputersService(instance=club_branch).run()


@cel_app.task
def synchronize_gizmo_computers_state():
    for club_branch in ClubBranch.objects.filter(is_active=True):
        GizmoGetComputersService(instance=club_branch).run()