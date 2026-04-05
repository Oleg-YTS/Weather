"""
Сервис донатов через Telegram Stars.
Простая кнопка «Поблагодарить» за 1 звезду.
"""

from aiogram.types import LabeledPrice
from aiogram import Bot
from logging import getLogger

logger = getLogger(__name__)

XTR_CURRENCY = "XTR"
DONATE_STARS = 1


def create_donate_price() -> list:
    """Создать платёж в Telegram Stars"""
    return [LabeledPrice(label="Поблагодарить", amount=DONATE_STARS)]


DONATE_INFO = {
    "title": "⭐ Поблагодарить — 1 звезда",
    "description": "Спасибо за поддержку проекта!",
    "payload": "donate_1_star",
    "thanks_text": "🙏 Спасибо за поддержку! Это очень много значит для меня!",
}


async def send_donate_invoice(
    bot: Bot,
    chat_id: int,
    stars: int = DONATE_STARS,
) -> bool:
    """Отправить инвойс на донат через Telegram Stars"""
    prices = create_donate_price()

    try:
        await bot.send_invoice(
            chat_id=chat_id,
            title=DONATE_INFO["title"],
            description=DONATE_INFO["description"],
            payload=DONATE_INFO["payload"],
            provider_token="",  # Пусто = Telegram Stars
            currency=XTR_CURRENCY,
            prices=prices,
        )
        return True
    except Exception as e:
        logger.warning(f"Не удалось отправить инвойс: {e}")
        return False


def create_donate_keyboard():
    """Inline-кнопка для доната"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❤️ Поблагодарить — 1 ⭐",
                    callback_data="donate_1",
                ),
            ],
        ]
    )
