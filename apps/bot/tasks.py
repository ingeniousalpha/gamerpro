import re
import time
from django.utils import timezone

import telegram
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode

from apps.bookings.tasks import gizmo_bro_add_time_and_set_booking_expiration
from apps.clubs.models import ClubBranchUser, ClubBranch
from apps.integrations.gizmo.exceptions import GizmoLoginAlreadyExistsError
from apps.integrations.gizmo.users_services import GizmoCreateUserService, GizmoGetUserByUsernameService, \
    GizmoUpdateUserByIDService
from apps.payments import PaymentStatuses
from config.celery_app import cel_app
from django.conf import settings


@cel_app.task
def bot_notify_about_new_user_task(club_branch_id, login, first_name, approved=False):
    club_branch = ClubBranch.objects.get(id=club_branch_id)
    if not club_branch.admins.exists() or not settings.TELEGRAM_BOT_TOKEN:
        return

    full_text = f"Новый пользователь:\n" \
                f"login: {login}\n" \
                f"name: {first_name}\n"
    admin = club_branch.admins.filter(is_active=True).last()
    bot = telegram.Bot(token=settings.TELEGRAM_BOT_TOKEN)
    if approved:
        bot.send_message(
            chat_id=admin.tg_chat_id,
            text=full_text + "\n<b>Верифицирован</b>",
            parse_mode=ParseMode.HTML,
        )
    else:
        bot.send_message(
            chat_id=admin.tg_chat_id,
            text=full_text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Показал удос ✅", callback_data=f"user_approved={login}|{club_branch_id}")]]
            ),
        )


@cel_app.task
def bot_approve_user_from_admin_task(club_branch_user_id):
    club_user = ClubBranchUser.objects.filter(id=club_branch_user_id).first()
    if not club_user:
        return

    bot_create_gizmo_user_task(
        club_branch_user_login=club_user.login,
        club_branch_id=club_user.club_branch.id
    )
    bot_notify_about_new_user_task(
        club_user.club_branch.id,
        club_user.login,
        club_user.first_name,
        approved=True
    )


@cel_app.task
def bot_create_gizmo_user_task(club_branch_user_login, club_branch_id):
    club_user = ClubBranchUser.objects.get(
        club_branch_id=club_branch_id,
        login=club_branch_user_login,
        gizmo_id__isnull=True,
    )
    if not club_user:
        return

    club_branch = club_user.club_branch
    # TODO: create this user in every branch

    # TODO: check if him already exist
    try:
        gizmo_user_id = GizmoCreateUserService(
            instance=club_branch,
            login=club_user.login,
            first_name=club_user.first_name,
            mobile_phone=club_user.gizmo_phone,
        ).run()
        club_user.gizmo_id = gizmo_user_id
        club_user.save(update_fields=['gizmo_id'])
    except GizmoLoginAlreadyExistsError as e:
        club_user = GizmoGetUserByUsernameService(
            instance=club_branch, username=club_user.login
        ).run()
        GizmoUpdateUserByIDService(
            instance=club_branch,
            user_id=club_user.gizmo_id,
            mobile_phone=club_user.gizmo_phone,
            first_name=club_user.first_name
        ).run()

    # create in all other BRO branches
    for branch in ClubBranch.objects.filter(club=club_branch.club).exclude(id__in=[club_branch.id]):
        branch_club_user = ClubBranchUser.objects.filter(club_branch=branch, login=club_user.login).first()

        if not branch_club_user:
            branch_club_user = ClubBranchUser.objects.create(
                club_branch=branch,
                login=club_user.login,
                user=club_user.user,
                gizmo_id=None,
                gizmo_phone=club_user.gizmo_phone,
                first_name=club_user.first_name,
            )

        if branch_club_user and not branch_club_user.user:
            branch_club_user.user = club_user.user
            branch_club_user.save()

        if branch_club_user and not branch_club_user.gizmo_id:
            try:
                gizmo_user_id = GizmoCreateUserService(
                    instance=branch,
                    login=club_user.login,
                    first_name=club_user.first_name,
                    mobile_phone=club_user.gizmo_phone,
                ).run()
                branch_club_user.gizmo_id = gizmo_user_id
                branch_club_user.save(update_fields=['gizmo_id'])
            except GizmoLoginAlreadyExistsError as e:
                branch_club_user = GizmoGetUserByUsernameService(
                    instance=branch, username=club_user.login
                ).run()
                branch_club_user.user = club_user.user

                GizmoUpdateUserByIDService(
                    instance=club_branch,
                    user_id=branch_club_user.gizmo_id,
                    mobile_phone=club_user.gizmo_phone,
                    first_name=club_user.first_name
                ).run()

                branch_club_user.gizmo_phone = club_user.gizmo_phone
                branch_club_user.first_name = club_user.first_name
                branch_club_user.save()
            except Exception:
                continue

    booking = club_user.bookings.last()
    if booking and booking.payments.filter(status=PaymentStatuses.PAYMENT_APPROVED).exists():
        gizmo_bro_add_time_and_set_booking_expiration(str(booking.uuid))
