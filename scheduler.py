import logging
import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from services.user_data_service import get_all_users
from services.weather_service import get_weather
from services.horoscope_service import get_horoscope
from services.donate_service import create_donate_keyboard

load_dotenv()

logger = logging.getLogger(__name__)

# Часовой пояс из .env (по умолчанию Europe/Moscow)
TIMEZONE = os.getenv("TIMEZONE", "Europe/Moscow")


def create_scheduler(bot: Bot) -> AsyncIOScheduler:
    """Создать и настроить планировщик задач"""
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)

    # Задача每天早上 8:00
    scheduler.add_job(
        send_morning_update,
        CronTrigger(hour=8, minute=0, timezone=TIMEZONE),
        args=[bot],
        id="morning_update",
        replace_existing=True,
    )

    # Дополнительная задача в 12:00 (если утром не дошло)
    scheduler.add_job(
        send_morning_update,
        CronTrigger(hour=12, minute=0, timezone=TIMEZONE),
        args=[bot],
        id="backup_update",
        replace_existing=True,
    )

    logger.info(f"Планировщик запущен. Рассылка в 8:00 и 12:00 по {TIMEZONE}")

    # Выводим все запланированные задачи
    for job in scheduler.get_jobs():
        logger.info(f"Запланирована задача: {job.name} -> {job.trigger}")

    return scheduler


async def send_morning_update(bot: Bot):
    """Отправить утреннюю рассылку всем пользователям"""
    logger.info("Начало утренней рассылки")

    users = get_all_users()

    if not users:
        logger.info("Нет пользователей для рассылки")
        return

    sent_count = 0
    error_count = 0

    for user in users:
        if not user.has_settings():
            logger.info(f"Пользователь {user.telegram_id} ещё не настроил данные")
            continue

        # Формируем сообщение
        message_parts = ["🌅 **Доброе утро!**\n"]

        for city in user.cities:
            weather = get_weather(city)
            if weather:
                message_parts.append(weather)
            else:
                message_parts.append(f"❌ Не удалось получить погоду для {city}")

        horoscope = get_horoscope(user.zodiac_sign, getattr(user, "horoscope_persona", "normal"))
        if horoscope:
            message_parts.append(horoscope)
        else:
            message_parts.append(f"❌ Не удалось получить гороскоп")

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="➕ Добавить город", callback_data="add_city")],
                [InlineKeyboardButton(text="➖ Удалить город", callback_data="remove_city")],
            ]
        )

        full_message = "\n\n".join(message_parts)

        # Повторные попытки при ошибке отправки (до 3 раз)
        for attempt in range(3):
            try:
                # Основное сообщение с погодой и гороскопом
                main_msg = await bot.send_message(
                    chat_id=user.telegram_id,
                    text=full_message,
                    reply_markup=keyboard,
                    parse_mode="Markdown",
                )

                # Кнопка доната
                await bot.send_message(
                    chat_id=user.telegram_id,
                    text="☕ Если бот полезен — поблагодарите звёздочкой!",
                    reply_markup=create_donate_keyboard(),
                )

                sent_count += 1
                logger.info(f"✅ Отправлено пользователю {user.telegram_id}")
                break

            except Exception as e:
                error_count += 1
                wait_time = (attempt + 1) * 5  # 5, 10, 15 секунд
                logger.warning(
                    f"Ошибка отправки пользователю {user.telegram_id} (попытка {attempt + 1}/3): {e}. "
                    f"Ждём {wait_time}с..."
                )
                if attempt < 2:
                    import asyncio
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"❌ Не удалось отправить пользователю {user.telegram_id} после 3 попыток")

    logger.info(f"Рассылка завершена. Отправлено: {sent_count}, Ошибок: {error_count}")
