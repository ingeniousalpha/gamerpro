import logging

from constance import config
from django.core.cache import cache

from apps.bookings import BookingStatuses
from apps.bookings.models import Booking
from apps.clubs import SoftwareTypes
from apps.clubs.services import add_cashback, subtract_cashback
from apps.clubs.tasks import _sync_club_branch_computers
from apps.integrations.gizmo.computers_services import GizmoLockComputerService, GizmoUnlockComputerService
from apps.integrations.gizmo.deposits_services import GizmoCreateDepositTransactionService
from apps.integrations.gizmo.time_packets_services import (
    GizmoAddPaidTimeToUser, GizmoSetTimePacketToUser, GizmoSetPointsToUser
)
from apps.integrations.gizmo.users_services import GizmoStartUserSessionService, GizmoEndUserSessionService
from apps.integrations.senet.computer_services import SenetLockComputersService, SenetUnlockComputersService
from apps.integrations.senet.deposit_services import SenetReplenishUserBalanceService
from apps.notifications.tasks import fcm_push_notify_user
from apps.payments import PaymentStatuses
from apps.payments.models import Payment
from config.celery_app import cel_app

logger = logging.getLogger("bookings")

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
    print("inside gizmo_book_computers")
    booking = Booking.objects.filter(uuid=booking_uuid).first()
    if not booking:
        return

    if not from_balance and not booking.time_packet:
        GizmoCreateDepositTransactionService(
            instance=booking.club_branch,
            user_gizmo_id=booking.club_user.outer_id,
            booking=booking,
            user_received_amount=booking.amount,
            commission_amount=booking.commission_amount,
            total_amount=booking.total_amount
        ).run()
    elif booking.time_packet:
        print('booking time_packet activating...')
        if Booking.objects.filter(club_user__user=booking.club_user.user).count() <= 1:
            extra_minutes = config.EXTRA_MINUTES_TO_FIRST_TRANSACTION  # add extra hour
            GizmoAddPaidTimeToUser(
                instance=booking.club_branch,
                user_id=booking.club_user.outer_id,
                minutes=extra_minutes,
                price=booking.time_packet.price
            ).run()
        GizmoSetTimePacketToUser(
            instance=booking.club_branch,
            user_id=booking.club_user.outer_id,
            product_id=booking.time_packet.outer_id
        ).run()
        if config.CASHBACK_TURNED_ON and booking.amount >= 100:
            add_cashback(
                user=booking.club_user.user,
                club=booking.club_branch.club,
                from_amount=booking.total_amount
            )
        print('booking time_packet activated')
    for booked_computer in booking.computers.all():
        GizmoLockComputerService(
            instance=booking.club_branch,
            computer_id=booked_computer.computer.outer_id
        ).run()
        booked_computer.computer.is_locked = True
        booked_computer.computer.save(update_fields=['is_locked'])

    unlock_computers_and_make_booking_expired.apply_async(
        (str(booking.uuid),),
        countdown=config.FREE_SECONDS_BEFORE_START_TARIFFING
    )


@cel_app.task
def gizmo_bro_add_time_and_set_booking_expiration(booking_uuid, by_points=False, check_status=True):
    booking = (Booking.objects.select_related(
        'club_user', 'club_user__user', 'club_branch', 'club_branch__club', 'time_packet'
    ).prefetch_related('computers').filter(uuid=booking_uuid).first())
    print(f"uuid: {booking_uuid}, booking.status: {booking.status if booking else ''}", )
    if not booking or (check_status and booking.status in [BookingStatuses.SESSION_STARTED, BookingStatuses.PLAYING]):
        return

    from apps.bot.tasks import bot_notify_about_booking_task
    user = booking.club_user.user
    club = booking.club_branch.club

    print(f"BRO booking({str(booking.uuid)}) time_packet activating...")

    if delayed_times := user.delayed_time_set.filter(club=club):
        for delayed in delayed_times:
            if delayed.booking.uuid != booking.uuid:
                # SET TIME PACKET FOR FIRSTLY CANCELLED BOOKINGS OF UNVERIFIED CLUB USER
                GizmoSetTimePacketToUser(
                    instance=delayed.booking.club_branch,
                    user_id=delayed.booking.club_user.outer_id,
                    product_id=delayed.time_packet.outer_id
                ).run()
        delayed_times.delete()

    if extra_minutes := club.get_perk("EXTRA_MINUTES_TO_FIRST_TRANSACTION") \
            and not user.is_used_perk("EXTRA_MINUTES_TO_FIRST_TRANSACTION"):
        GizmoAddPaidTimeToUser(
            instance=booking.club_branch,
            user_id=booking.club_user.outer_id,
            minutes=extra_minutes,
            price=booking.time_packet.price
        ).run()
        user.use_perk(club, "EXTRA_MINUTES_TO_FIRST_TRANSACTION")

    if by_points:
        GizmoSetPointsToUser(
            instance=booking.club_branch,
            user_id=booking.club_user.outer_id,
            amount=booking.time_packet.price
        ).run()

    GizmoSetTimePacketToUser(
        instance=booking.club_branch,
        user_id=booking.club_user.outer_id,
        product_id=booking.time_packet.outer_id,
        by_points=by_points,
    ).run()

    if by_points:
        subtract_cashback(
            user=user, club=club, amount=booking.time_packet.price
        )

    if config.CASHBACK_TURNED_ON and not by_points and booking.amount >= 100:
        add_cashback(
            user=user, club=club, from_amount=booking.total_amount
        )

    print(f"BRO booking({str(booking.uuid)}) time_packet activated")
    booking.is_time_packet_set = True
    booking.save()

    bot_notify_about_booking_task.delay(
        club_branch_id=booking.club_branch.id,
        booking_uuid=booking.uuid,
        booking_created_at=booking.created_at.astimezone().strftime('%H:%M:%S %d.%m.%Y'),
        login=booking.club_user.login,
        time_packet_name=booking.time_packet.display_name,
        computers=[str(bc.computer.number) for bc in booking.computers.all()]
    )
    unlock_computers_and_make_booking_expired.apply_async(
        (str(booking.uuid),),
        countdown=config.FREE_SECONDS_BEFORE_START_TARIFFING
    )


@cel_app.task
def gizmo_start_user_session(booking_uuid):
    # TODO: Override function for several computers.
    #  Now it fits only for 1 computer booked

    booking = Booking.objects.filter(uuid=booking_uuid).first()
    if not booking:
        return
    elif booking.status != BookingStatuses.ACCEPTED:
        return

    booking.status = BookingStatuses.SESSION_STARTED
    booking.save(update_fields=['status'])
    # todo: check is user session already started?
    computer_gizmo_id = booking.computers.first().computer.outer_id
    GizmoStartUserSessionService(
        instance=booking.club_branch,
        user_id=booking.club_user.outer_id,
        computer_id=computer_gizmo_id
    ).run()
    send_push_about_booking_status(booking.uuid, BookingStatuses.SESSION_STARTED)


@cel_app.task
def cancel_booking(booking_uuid):
    booking = (
        Booking.objects
        .filter(uuid=booking_uuid)
        .select_related('club_user__user', 'club_branch__club')
        .first()
    )
    if not booking:
        return

    unlock_computers(booking.uuid)
    if booking.club_branch.club.software_type == SoftwareTypes.GIZMO and booking.club_user.is_verified:
        GizmoEndUserSessionService(
            instance=booking.club_branch,
            user_id=booking.club_user.outer_id
        ).run()
    # cel_app.send_task(
    #     name="apps.bookings.tasks.gizmo_unlock_computers",
    #     args=[booking.uuid],
    # )


@cel_app.task
def unlock_computers_and_make_booking_expired(booking_uuid):
    booking = Booking.objects.filter(uuid=booking_uuid).first()
    if not booking or booking.status != BookingStatuses.ACCEPTED:
        return

    booking.status = BookingStatuses.EXPIRED
    booking.save(update_fields=['status'])
    unlock_computers(booking_uuid, False)



@cel_app.task
def unlock_computers(booking_uuid, check_payment=False):
    booking = (
        Booking.objects
        .filter(uuid=booking_uuid)
        .select_related('club_branch__club')
        .prefetch_related('computers')
        .first()
    )
    if not booking:
        return

    # TODO: rewrite this
    if check_payment and (booking.payments.filter(status=PaymentStatuses.PAYMENT_APPROVED).exists() or booking.use_cashback):
        return

    software_type = booking.club_branch.club.software_type
    booked_computers = booking.computers.all().select_related('computer')
    if software_type == SoftwareTypes.GIZMO:
        for booked_computer in booked_computers:
            GizmoUnlockComputerService(
                instance=booking.club_branch,
                computer_id=booked_computer.computer.outer_id
            ).run()
            cache.delete(f'BOOKING_STATUS_COMP_{booked_computer.computer.id}')
    elif software_type == SoftwareTypes.SENET:
        for booked_computer in booked_computers:
            SenetUnlockComputersService(
                instance=booking.club_branch,
                computers=[booked_computer.computer.outer_id]
            ).run()
            cache.delete(f'BOOKING_STATUS_COMP_{booked_computer.computer.id}')

    _sync_club_branch_computers(booking.club_branch)


@cel_app.task
def gizmo_unlock_computers_and_start_user_session(booking_uuid):
    booking = Booking.objects.filter(uuid=booking_uuid).first()
    if not booking:
        return

    for index, booked_computer in enumerate(booking.computers.all()):
        GizmoUnlockComputerService(
            instance=booking.club_branch,
            computer_id=booked_computer.computer.outer_id
        ).run()
        if index == 0:
            GizmoStartUserSessionService(
                instance=booking.club_branch,
                user_id=booking.club_user.outer_id,
                computer_id=booked_computer.computer.outer_id
            ).run()
            cache.delete(f'BOOKING_STATUS_COMP_{booked_computer.computer.id}')
        else:
            cache.set(f'BOOKING_STATUS_COMP_{booked_computer.computer.id}', True, config.MULTIBOOKING_LAUNCHING_TIME*60)

    _sync_club_branch_computers(booking.club_branch)


def lock_computers(booking_uuid, unlock_after=config.PAYMENT_EXPIRY_TIME):
    """unlock_after - in minutes"""

    booking = (
        Booking.objects
        .filter(uuid=booking_uuid)
        .select_related('club_branch__club')
        .prefetch_related('computers')
        .first()
    )
    if not booking:
        return

    software_type = booking.club_branch.club.software_type
    booked_computers = booking.computers.all().select_related('computer')
    is_locked = False
    if software_type == SoftwareTypes.GIZMO:
        for booked_computer in booked_computers:
            GizmoLockComputerService(instance=booking.club_branch, computer_id=booked_computer.computer.outer_id).run()
        is_locked = True
    elif software_type == SoftwareTypes.SENET:
        SenetLockComputersService(
            instance=booking.club_branch,
            computers=[booked_computer.computer.outer_id for booked_computer in booked_computers]
        ).run()
        is_locked = True

    if is_locked:
        unlock_computers.apply_async((str(booking.uuid), True), countdown=unlock_after * 60)
        unlock_computers_and_make_booking_expired(
            (str(booking.uuid),),
            countdown=config.FREE_SECONDS_BEFORE_START_TARIFFING
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


@cel_app.task
def senet_replenish_user_balance(booking_uuid, use_cashback=False):
    logger.info(f"({booking_uuid}) Task senet_replenish_user_balance started")
    booking = (
        Booking.objects
        .filter(uuid=booking_uuid)
        .select_related('club_user__user', 'club_branch__club')
        .first()
    )
    if not booking:
        logger.error(f"({booking_uuid}) Task senet_replenish_user_balance failed: Booking not found")
        return False
    if booking.club_branch.club.software_type != SoftwareTypes.SENET:
        logger.error(f"({booking_uuid}) Task senet_replenish_user_balance failed: Invalid software type")
        return False
    if use_cashback:
        if not subtract_cashback(booking.club_user.user, booking.club_branch.club, booking.amount):
            logger.error(f"({booking_uuid}) Task senet_replenish_user_balance failed: Cashback subtraction error")
            return False
    elif Payment.objects.filter(booking=booking, status=PaymentStatuses.PAYMENT_APPROVED).exists():
        logger.error(f"({booking_uuid}) Task senet_replenish_user_balance failed: Invalid payment status")
        return False
    SenetReplenishUserBalanceService(
        instance=booking.club_branch,
        account_id=booking.club_user.outer_id,
        amount=booking.amount
    ).run()
    logger.info(f"({booking_uuid}) Task senet_replenish_user_balance finished")
    return True
