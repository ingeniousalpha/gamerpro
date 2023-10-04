import time

from django.core.cache import cache

from apps.bookings import BookingStatuses
from apps.bookings.models import Booking
from apps.clubs.models import ClubBranch, ClubBranchUser, ClubComputer
from apps.clubs.tasks import _sync_gizmo_computers_state_of_club_branch
from apps.integrations.gizmo.computers_services import GizmoLockComputerService, GizmoUnlockComputerService
from apps.integrations.gizmo.deposits_services import GizmoCreateDepositTransactionService
from apps.integrations.gizmo.time_packets_services import GizmoAddPaidTimeToUser
from apps.integrations.gizmo.users_services import GizmoStartUserSessionService, GizmoEndUserSessionService
from apps.notifications.tasks import fcm_push_notify_user
from config.celery_app import cel_app
from constance import config


BOOKING_STATUS_TRANSITION_PUSH_TEXT = {
    BookingStatuses.ACCEPTED: {
        "title": "Компьютер успешно забронирован",
        "body": "В клубе нажми кнопку 'Разблокировать' чтобы включить компьютер.",
    },
    BookingStatuses.SESSION_STARTED: {
        "title": "Тарификация началась",
        "body": "Комп все еще за тобой, но с баланса запустилась тарификация",
    },
    BookingStatuses.PLAYING: {
        "title": "Начало игры",
        "body": "Приятной катки ;)",
    },
    BookingStatuses.COMPLETED: {
        "title": "Твоя сессия завершена",
        "body": "Отлично поиграл, приходи еще :)",
    },
    BookingStatuses.CANCELLED: {
        "title": "Бронь отменена",
        "body": "Надеемся что ты еще вернешься",
    }
}


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
        booked_computer.computer.is_locked = True
        booked_computer.computer.save(update_fields=['is_locked'])
        gizmo_start_user_session.apply_async(
            (booking.uuid, booked_computer.computer.gizmo_id),
            countdown=config.FREE_SECONDS_BEFORE_START_TARIFFING
        )
    if booking.time_packet:
        GizmoAddPaidTimeToUser(
            instance=booking.club_branch,
            user_id=booking.club_user.gizmo_id,
            minutes=booking.time_packet.minutes,
            price=booking.time_packet.price
        ).run()


@cel_app.task
def gizmo_start_user_session(booking_uuid, computer_gizmo_id):
    booking = Booking.objects.filter(uuid=booking_uuid).first()
    if not booking:
        return
    elif booking.status != BookingStatuses.ACCEPTED:
        return

    booking.status = BookingStatuses.SESSION_STARTED
    booking.save(update_fields=['status'])
    # todo: check is user session already started?
    GizmoStartUserSessionService(
        instance=booking.club_branch,
        user_id=booking.club_user.gizmo_id,
        computer_id=computer_gizmo_id
    ).run()
    send_push_about_booking_status(booking.uuid, BookingStatuses.SESSION_STARTED)


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


@cel_app.task
def gizmo_unlock_computers_and_start_user_session(booking_uuid):
    booking = Booking.objects.filter(uuid=booking_uuid).first()
    if not booking:
        return

    for booked_computer in booking.computers.all():
        GizmoUnlockComputerService(
            instance=booking.club_branch,
            computer_id=booked_computer.computer.gizmo_id
        ).run()
        cache.delete(f'BOOKING_STATUS_COMP_{booked_computer.computer.id}')
        GizmoStartUserSessionService(
            instance=booking.club_branch,
            user_id=booking.club_user.gizmo_id,
            computer_id=booked_computer.computer.gizmo_id
        ).run()

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


@cel_app.task
def send_push_about_booking_status(booking_uuid, status):
    booking = Booking.objects.filter(uuid=booking_uuid).first()
    if not booking:
        return

    if not booking.club_user.user.fb_tokens.exists():
        return

    fcm_push_notify_user(
        tokens=[booking.club_user.user.fb_tokens.first().token],
        data={
            "title": BOOKING_STATUS_TRANSITION_PUSH_TEXT[status]["title"],
            "body": BOOKING_STATUS_TRANSITION_PUSH_TEXT[status]["body"],
        }
    )
