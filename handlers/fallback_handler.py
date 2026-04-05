import logging

from aiogram import Router, F
from aiogram.types import Message

logger = logging.getLogger(__name__)

router = Router()


@router.message(F.text.startswith("/"))
async def unknown_command(message: Message):
    """Обработка неизвестных команд"""
    await message.answer(
        "🤔 Не понимаю эту команду.\n\n"
        "Нажми кнопку **Start** внизу экрана для начала работы.",
        parse_mode="Markdown",
    )


@router.message()
async def unknown_message(message: Message):
    """Обработка неизвестных текстовых сообщений"""
    await message.answer(
        "🤔 Не понимаю это сообщение.\n\n"
        "Нажми кнопку **Start** или введи название города."
    )
