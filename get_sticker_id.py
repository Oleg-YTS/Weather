"""
Быстрый скрипт для получения sticker_id.
Отправьте боту любой стикер и посмотрите ID в логе.
"""
import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from dotenv import load_dotenv

load_dotenv()

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "👋 Отправьте мне любой стикер, "
        "и я покажу его ID для вставки в код!"
    )


@dp.message(F.sticker)
async def show_sticker_id(message: Message):
    sticker = message.sticker
    sticker_id = sticker.file_id
    emoji = sticker.emoji or ""
    
    text = (
        f"📋 **Sticker ID:**\n"
        f"```\n{sticker_id}\n```\n\n"
        f"Эмодзи: {emoji}\n"
        f"Набор: {sticker.set_name or 'N/A'}\n\n"
        f"Скопируйте ID и вставьте в `donate_service.py`"
    )
    
    await message.answer(text, parse_mode="Markdown")


async def main():
    print("🎯 Sticker ID Grabber запущен!")
    print(f"Бот: @{(await bot.get_me()).username}")
    print("Отправьте стикер боту в Telegram...\n")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
