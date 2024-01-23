import asyncio
import logging
import sys
import asyncpg
import redis
import json
import datetime

from os import getenv
from celery import Celery
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.utils.markdown import hbold
import os
import sys

# Add the parent directory of the current script to the Python path
sys.path.append("/googlegram")
sys.path.append("/googlegram/")
sys.path.append("/googlegram/apps")
sys.path.append("/googlegram/apps/")
sys.path.append("/googlegram/apps/bot")
sys.path.append("/googlegram/apps/bot/")
sys.path.append("/googlegram/apps/common")
sys.path.append("/googlegram/apps/common/")
# print(os.path.dirname(os.path.abspath(__file__)))

TOKEN = getenv("TELEGRAM_BOT_TOKEN", "6414695545:AAFILR0doVjiukYMtiTOCzbCPKS-8NFkbQo")

# All handlers should be attached to the Router (or Dispatcher)
dp = Dispatcher()
chosen_categories = dict()
DB_HOST = getenv("DB_HOST", "localhost")
DB_PORT = getenv("DB_PORT", "5432")
DB_NAME = getenv("DB_NAME", "gamerprodb")
DB_USER = getenv("DB_USER", "gamerprodb")
DB_PASSWORD = getenv("DB_PASSWORD", "gamerprodb")

REDIS_HOST = getenv("REDIS_HOST", "localhost")
REDIS_PORT = getenv("REDIS_PORT", "6379")
REDIS_DB_FOR_CELERY = getenv("REDIS_DB_FOR_CELERY", "0")
REDIS_DB_FOR_CACHE = getenv("REDIS_DB_FOR_CACHE", "1")

REDIS_BROKER_URL = "redis://{host}:{port}/{db_index}".format(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db_index=REDIS_DB_FOR_CELERY,
)
REDIS_CASHE_URL = "redis://{host}:{port}/{db_index}".format(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db_index=REDIS_DB_FOR_CACHE,
)
app = Celery("googlegram", broker=REDIS_BROKER_URL)


async def create_db_pool():
    return await asyncpg.create_pool(
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        host=DB_HOST,
    )


def get_phone_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="Поделиться номером телефона", request_contact=True)
    return builder.as_markup(resize_keyboard=True)


def get_club_branches_keyboard(db_club_branches):
    if not db_club_branches:
        return

    buttons = [
        [types.InlineKeyboardButton(
            text=dbclub.get('name'),
            callback_data=f"club_branch={dbclub.get('id')}")
        ] for dbclub in db_club_branches
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    if message.from_user.is_bot:
        return

    hey_msg = f"Привет, {hbold(message.from_user.full_name)}! \n\n" \
              f"Это <b>Gamer Pro Admin</b> Бот.\n" \
              f"Отправь cвой сотовый номер, и мы проверим тебя в базе"

    pool = await create_db_pool()
    async with pool.acquire() as connection:
        admin = await connection.fetchrow(
            f"SELECT * FROM clubs_clubbranchadmin WHERE tg_chat_id = $1",
            str(message.chat.id)
        )
        if not admin:
            await message.answer(hey_msg, reply_markup=get_phone_keyboard())
        else:
            await message.answer("Ты уже зарегистрированный админ!")
    await pool.close()


@dp.message(F.text, Command("info"))
async def command_info_handler(message: Message) -> None:
    if message.from_user.is_bot:
        return

    pool = await create_db_pool()
    async with pool.acquire() as connection:
        admin = await connection.fetchrow(
            f"SELECT a.id, a.tg_chat_id, a.is_active, cb.name FROM clubs_clubbranchadmin a "
            f"JOIN clubs_clubbranch cb on a.club_branch_id=cb.id "
            f"WHERE tg_chat_id = $1",
            str(message.chat.id)
        )
        print(admin)
        status = "На смене" if admin.get('is_active') else "Не на смене"

    await pool.close()
    await message.answer(
        f"Ты админ в точке: {admin.get('name')}\n"
        f"Статус: <b>{status}</b>"
    )


@dp.message(F.text, Command("onshift"))
async def command_info_handler(message: Message) -> None:
    if message.from_user.is_bot:
        return

    pool = await create_db_pool()
    async with pool.acquire() as connection:
        admin = await connection.fetchrow(
            f"SELECT * FROM clubs_clubbranchadmin a "
            f"WHERE tg_chat_id = $1",
            str(message.chat.id)
        )
        print(admin)
        async with connection.transaction():
            await connection.execute(
                "UPDATE clubs_clubbranchadmin SET is_active = $1 WHERE club_branch_id = $2",
                False, admin.get('club_branch_id'),
            )
            await connection.execute(
                "UPDATE clubs_clubbranchadmin SET is_active = $1 WHERE tg_chat_id = $2",
                True, admin.get('tg_chat_id'),
            )
    await pool.close()
    await message.answer("Ты теперь на смене")


@dp.message(F.contact)
async def get_admin_mobile_phone(message: types.Message) -> None:

    try:
        print(message)
        print(message.contact.phone_number)
        mobile_phone = f"+{message.contact.phone_number}"

        pool = await create_db_pool()
        async with pool.acquire() as connection:
            admin = await connection.fetchrow(f"SELECT * FROM clubs_clubbranchadmin WHERE mobile_phone = $1", mobile_phone)
            print(admin)

            if admin:
                async with connection.transaction():
                    await connection.execute(
                        "UPDATE clubs_clubbranchadmin SET tg_chat_id = $1, tg_username = $2 WHERE id = $3",
                        str(message.chat.id),
                        str(message.chat.username),
                        admin.get('id')
                    )
                # TODO: fetch all BRO club branches
                clubs = await connection.fetch(f"SELECT * FROM clubs_clubbranch WHERE club_id = 2")
                await message.answer("OK, твой телефон подтвержден 👍\n\nТеперь выбери точку клуба:", reply_markup=get_club_branches_keyboard(clubs))
            else:
                await message.answer("Такого номера не найдено")
        await pool.close()
    except TypeError:
        # But not all the types is supported to be copied so need to handle it
        await message.answer("Nice try!")


async def main() -> None:
    # Initialize Bot instance with a default parse mode which will be passed to all API calls
    bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
    # And the run events dispatching
    await dp.start_polling(bot)


# class ClientSession:
#     _sessions = dict()
#     redis_client = None
#
#     @classmethod
#     def get(cls, chat_id, rclient=None, close_conn=False):
#         if not rclient:
#             rclient = redis.from_url(REDIS_CASHE_URL)
#             close_conn = True
#
#         client_data = rclient.get(chat_id)
#         if client_data:
#             client_data = json.loads(client_data)
#
#         if close_conn:
#             rclient.close()
#
#         return client_data or {}
#
#     @classmethod
#     def set(cls, chat_id, key, value):
#         rclient = redis.from_url(REDIS_CASHE_URL)
#         client_data = cls.get(chat_id, rclient=rclient)
#
#         client_data[key] = value
#         rclient.set(chat_id, json.dumps(client_data))
#         rclient.close()
#
#     @classmethod
#     def set_from_db(cls, chat_id, client_db):
#         rclient = redis.from_url(REDIS_CASHE_URL)
#         client_data = cls.get(chat_id, rclient=rclient)
#
#         client_data.update({
#             "client_id": client_db.get('id'),
#             "tg_chat_id": client_db.get('tg_chat_id'),
#             "is_tg_premium": client_db.get('is_tg_premium'),
#             "used_trial": client_db.get('used_trial'),
#             "msg_type": client_db.get('msg_type'),
#         })
#         rclient.set(chat_id, json.dumps(client_data))
#         rclient.close()


def get_subscription_plans_keyboard(db_plans, used_trial=False):
    buttons = [
        [types.InlineKeyboardButton(
            text=f"{p.get('name')} - {p.get('amount')} KZT",
            callback_data=f"plan={p.get('code')}")
        ] for p in db_plans if p.get('code') != "trial"
    ]
    if not used_trial:
        buttons.append([
            types.InlineKeyboardButton(text="Активировать Пробный день", callback_data="plan=trial")
        ])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


async def get_categories_from_db():
    pool = await create_db_pool()
    async with pool.acquire() as connection:
        db_categories = await connection.fetch(f"SELECT * FROM common_category")
        print(db_categories)
    await pool.close()
    return db_categories


@dp.callback_query(F.data.startswith("club_branch="))
async def choose_club_branch(callback: types.CallbackQuery):
    club_branch_id = callback.data.split('=')[1]

    pool = await create_db_pool()
    async with pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                "UPDATE clubs_clubbranchadmin SET club_branch_id = $1 WHERE tg_chat_id = $2",
                int(club_branch_id),
                str(callback.message.chat.id),
            )

        await callback.message.answer(
            "Сохранено! Теперь ты будешь получать уведомления о новых зарегистрированных юзерах",
            reply_markup=types.ReplyKeyboardRemove()
        )
    await pool.close()


@dp.callback_query(F.data.startswith("user_verified="))
async def choose_plan(callback: types.CallbackQuery):
    user_login = str(callback.data.split('user_verified=')[1])
    app.send_task(
        name="apps.bot.tasks.bot_create_gizmo_user_task",
        args=[user_login]
    )
    await callback.message.edit_text(
        text=callback.message.text + "\n\n<b>Верифицирован</b>"
    )
    await callback.message.edit_reply_markup(reply_markup=types.ReplyKeyboardRemove())
    await callback.answer(text="Юзер верифицирован, его сессия запускается...", show_alert=True)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
