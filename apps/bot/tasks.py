import re
import time
from django.utils import timezone

import telegram
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode

from apps.clubs.models import ClubBranchUser, ClubBranch
from apps.integrations.gizmo.users_services import GizmoCreateUserService
from config.celery_app import cel_app
from django.conf import settings


@cel_app.task
def bot_notify_about_new_user_task(club_branch_id, login, first_name):
    club_branch = ClubBranch.objects.get(id=club_branch_id)
    if not club_branch.admins.exists() or not settings.TELEGRAM_BOT_TOKEN:
        return

    full_text = f"Новый пользователь:\n" \
                f"login: {login}\n" \
                f"name: {first_name}\n"
    admin = club_branch.admins.filter(is_active=True).first()
    bot = telegram.Bot(token=settings.TELEGRAM_BOT_TOKEN)
    bot.send_message(
        chat_id=admin.tg_chat_id,
        text=full_text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Проверено✅", callback_data=f"user_verified={login}")]]
        ),
    )


@cel_app.task
def bot_create_gizmo_user_task(club_branch_user_login):
    club_user = ClubBranchUser.objects.get(login=club_branch_user_login)
    if not club_user:
        return

    club_branch = club_user.club_branch
    gizmo_user_id = GizmoCreateUserService(
        instance=club_branch,
        login=club_user.login,
        first_name=club_user.first_name,
        mobile_phone=club_user.gizmo_phone,
    ).run()
    club_user.gizmo_id = gizmo_user_id
    club_user.save(update_fields=['gizmo_id'])
