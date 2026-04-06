import logging

from aiogram import Router, F
from aiogram.types import Message

from scheduler import send_morning_update
from services.user_data_service import get_all_users

logger = logging.getLogger(__name__)
router = Router()

# Ссылка на планировщик — устанавливается из main.py
_scheduler = None


def set_scheduler(s):
    global _scheduler
    _scheduler = s


@router.message(F.text == "/test")
async def cmd_test(message: Message):
    logger.info("Тестовая рассылка")
    await send_morning_update(message.bot)
    await message.answer("✅ Отправлено!")


@router.message(F.text == "/status")
async def cmd_status(message: Message):
    if not _scheduler:
        await message.answer("❌ Планировщик не запущен")
        return

    jobs = _scheduler.get_jobs()
    text = "📊 **Планировщик**\n\n"
    for j in jobs:
        text += f"⏰ {j.name}\n   `{j.trigger}`\n"
        text += f"   {j.next_run_time.strftime('%d.%m %H:%M') if j.next_run_time else '⏸️'}\n\n"

    users = get_all_users()
    active = [u for u in users if u.has_settings()]
    text += f"👥 Всего: {len(users)}\n✅ Настроено: {len(active)}"

    await message.answer(text, parse_mode="Markdown")
