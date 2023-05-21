from apps.pipeline.gizmo.computers_services import GizmoLockComputerService
from apps.pipeline.gizmo.users_services import GizmoStartUserSessionService


def gizmo_book_computers(club_branch, club_user, computers):
    for computer in computers:
        GizmoStartUserSessionService(
            instance=club_branch,
            user_id=club_user.gizmo_id,
            computer_id=computer.gizmo_id
        ).run()
        GizmoLockComputerService(
            instance=club_branch,
            computer_id=computer.gizmo_id
        ).run()
        computer.is_booked = True
        computer.save()
