import logging

from aiogram import Router, F
from aiogram.types import Message

from scheduler import send_morning_update
from services.user_data_service import get_all_users

logger = logging.getLogger(__name__)

router = Router()


# Глобальная ссылка на планировщик — устанавливается из main.py
_scheduler_ref = None


def set_scheduler(scheduler):
    """Установить ссылку на планировщик (вызывается из main.py при запуске)"""
    global _scheduler_ref
    _scheduler_ref = scheduler


@router.message(F.text == "/test")
async def test_broadcast(message: Message):
    """Тестовая рассылка"""
    logger.info("Тестовая рассылка по команде /test")
    await send_morning_update(message.bot)
    await message.answer("✅ Тестовая рассылка отправлена!")


@router.message(F.text == "/status")
async def scheduler_status(message: Message):
    """Статус планировщика"""
    if not _scheduler_ref:
        await message.answer("❌ Планировщик не запущен")
        return

    jobs = _scheduler_ref.get_jobs()
    status_text = "📊 **Статус планировщика**\n\n"

    for job in jobs:
        status_text += f"⏰ {job.name}\n"
        status_text += f"   Триггер: `{job.trigger}`\n"
        if job.next_run_time:
            status_text += f"   Следующий запуск: {job.next_run_time.strftime('%d.%m.%Y %H:%M:%S')}\n"
        else:
            status_text += f"   Статус: ⏸️ На паузе\n"
        status_text += "\n"

    users = get_all_users()
    active_users = [u for u in users if u.has_settings()]

    status_text += f"👥 Всего пользователей: {len(users)}\n"
    status_text += f"✅ Настроенных пользователей: {len(active_users)}\n"

    await message.answer(status_text, parse_mode="Markdown")
