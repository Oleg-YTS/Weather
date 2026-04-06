import os
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from services.user_data_service import get_all_users
from services.weather_service import get_weather
from services.horoscope_service import get_horoscope
from services.donate_service import create_donate_keyboard
from services.persona_service import get_donate_message

load_dotenv()
logger = logging.getLogger(__name__)

TIMEZONE = os.getenv("TIMEZONE", "Europe/Moscow")


def create_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)

    scheduler.add_job(
        send_morning_update,
        CronTrigger(hour=8, minute=0, timezone=TIMEZONE),
        args=[bot],
        id="morning_update",
        replace_existing=True,
    )
    scheduler.add_job(
        send_morning_update,
        CronTrigger(hour=12, minute=0, timezone=TIMEZONE),
        args=[bot],
        id="backup_update",
        replace_existing=True,
    )

    logger.info(f"Планировщик: рассылка в 8:00 и 12:00 ({TIMEZONE})")
    for job in scheduler.get_jobs():
        logger.info(f"  ⏰ {job.name} -> {job.trigger}")

    return scheduler


async def send_morning_update(bot: Bot):
    logger.info("Начало утренней рассылки")
    users = get_all_users()
    if not users:
        return

    sent = 0
    for user in users:
        if not user.has_settings():
            continue

        parts = ["🌅 **Доброе утро!**"]
        for city in user.cities:
            w = get_weather(city)
            parts.append(w if w else f"❌ Нет данных для {city}")

        h = get_horoscope(user.zodiac_sign, user.horoscope_persona)
        parts.append(h if h else "❌ Нет гороскопа")

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="➕ Добавить город", callback_data="add_city")],
                [InlineKeyboardButton(text="➖ Удалить город", callback_data="remove_city")],
            ]
        )

        try:
            await bot.send_message(
                chat_id=user.telegram_id,
                text="\n\n".join(parts),
                reply_markup=keyboard,
                parse_mode="Markdown",
            )
            persona = user.horoscope_persona
            await bot.send_message(
                chat_id=user.telegram_id,
                text=get_donate_message(persona),
                reply_markup=create_donate_keyboard(persona),
            )
            sent += 1
        except Exception as e:
            logger.error(f"Ошибка отправки {user.telegram_id}: {e}")

    logger.info(f"Рассылка: отправлено {sent}/{len(users)}")
