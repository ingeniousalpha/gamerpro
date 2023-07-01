from apps.bookings.models import Booking
from apps.clubs.models import ClubBranch, ClubBranchUser, ClubComputer
from apps.integrations.gizmo.computers_services import GizmoLockComputerService, GizmoUnlockComputerService
from apps.integrations.gizmo.users_services import GizmoStartUserSessionService, GizmoEndUserSessionService
from config.celery_app import cel_app
from django.conf import settings


def gizmo_book_computers(club_branch, club_user, computers):
    for computer in computers:
        GizmoLockComputerService(
            instance=club_branch,
            computer_id=computer.gizmo_id
        ).run()
        computer.is_booked = True
        computer.save()
        start_user_session.apply_async(
            (club_branch.id, club_user.gizmo_id, computer.gizmo_id),
            countdown=settings.FREE_SECONDS_BEFORE_START_TARIFFING
        )


@cel_app.task
def start_user_session(club_branch_id, user_gizmo_id, computer_gizmo_id):
    club_branch = ClubBranch.objects.filter(id=club_branch_id).first()
    GizmoStartUserSessionService(
        instance=club_branch,
        user_id=user_gizmo_id,
        computer_id=computer_gizmo_id
    ).run()


@cel_app.task
def gizmo_cancel_booking(booking_uuid):
    booking = Booking.objects.filter(uuid=booking_uuid).first()
    if booking:
        club_branch = ClubBranch.objects.filter(id=booking.club_branch_id).first()
        GizmoEndUserSessionService(
            instance=club_branch,
            user_id=booking.club_user.gizmo_id
        ).run()
        booking.is_cancelled = True
        booking.save(update_fields=['is_cancelled'])
        gizmo_unlock_computers.delay(booking.uuid)


@cel_app.task
def gizmo_unlock_computers(booking_uuid):
    booking = Booking.objects.filter(uuid=booking_uuid).first()
    if booking:
        club_branch = ClubBranch.objects.filter(id=booking.club_branch_id).first()
        for booked_computer in booking.computers.all():
            GizmoUnlockComputerService(
                instance=club_branch,
                computer_id=booked_computer.computer.gizmo_id
            ).run()
