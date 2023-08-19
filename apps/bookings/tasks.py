from django.core.cache import cache

from apps.bookings.models import Booking
from apps.clubs.models import ClubBranch, ClubBranchUser, ClubComputer
from apps.clubs.tasks import _sync_gizmo_computers_state_of_club_branch
from apps.integrations.gizmo.computers_services import GizmoLockComputerService, GizmoUnlockComputerService
from apps.integrations.gizmo.deposits_services import GizmoCreateDepositTransactionService
from apps.integrations.gizmo.users_services import GizmoStartUserSessionService, GizmoEndUserSessionService
from config.celery_app import cel_app
from constance import config


def gizmo_book_computers(booking_uuid, from_balance=False):
    booking = Booking.objects.filter(uuid=booking_uuid).first()
    if not booking:
        return

    if not from_balance:
        GizmoCreateDepositTransactionService(
            instance=booking.club_branch,
            user_gizmo_id=booking.club_user.gizmo_id,
            booking=booking,
            amount=booking.amount,
            commission_amount=booking.commission_amount,
            total_amount=booking.total_amount
        ).run()
    for booked_computer in booking.computers.all():
        GizmoLockComputerService(
            instance=booking.club_branch,
            computer_id=booked_computer.computer.gizmo_id
        ).run()
        booked_computer.computer.is_booked = True
        booked_computer.computer.save()
        start_user_session.apply_async(
            (booking.club_branch.id, booking.club_user.gizmo_id, booked_computer.computer.gizmo_id),
            countdown=config.FREE_SECONDS_BEFORE_START_TARIFFING
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
    if not booking:
        return

    gizmo_unlock_computers(booking.uuid)
    club_branch = ClubBranch.objects.filter(id=booking.club_branch_id).first()
    GizmoEndUserSessionService(
        instance=club_branch,
        user_id=booking.club_user.gizmo_id
    ).run()
    # cel_app.send_task(
    #     name="apps.bookings.tasks.gizmo_unlock_computers",
    #     args=[booking.uuid],
    # )


@cel_app.task
def gizmo_unlock_computers(booking_uuid, check_payment=False):
    booking = Booking.objects.filter(uuid=booking_uuid).first()
    if not booking:
        return

    if check_payment and booking.payments.exists():
        return

    for booked_computer in booking.computers.all():
        GizmoUnlockComputerService(
            instance=booking.club_branch,
            computer_id=booked_computer.computer.gizmo_id
        ).run()
        cache.delete(f'BOOKING_STATUS_COMP_{booked_computer.computer.id}')

    _sync_gizmo_computers_state_of_club_branch(booking.club_branch)


def gizmo_lock_computers(booking_uuid):
    booking = Booking.objects.filter(uuid=booking_uuid).first()
    if not booking:
        return

    for booked_computer in booking.computers.all():
        GizmoLockComputerService(
            instance=booking.club_branch,
            computer_id=booked_computer.computer.gizmo_id
        ).run()

    gizmo_unlock_computers.apply_async(
        (str(booking.uuid), True),
        countdown=config.PAYMENT_EXPIRY_TIME*60
    )
