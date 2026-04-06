from aiogram import Router, F
from aiogram.types import Message

router = Router()


@router.message(F.text.startswith("/"))
async def unknown_cmd(message: Message):
    await message.answer(
        "🤔 Не понимаю эту команду.\n\n"
        "Нажми кнопку **Start** или введи название города.",
        parse_mode="Markdown",
    )


@router.message()
async def unknown_msg(message: Message):
    await message.answer(
        "🤔 Не понимаю.\n\n"
        "Нажми кнопку **Start** или введи название города."
    )
