from aiogram.types import LabeledPrice
from aiogram import Bot
from logging import getLogger

logger = getLogger(__name__)

XTR_CURRENCY = "XTR"
DONATE_STARS = 1

DONATE_INFO = {
    "title": "⭐ Поблагодарить — 1 звезда",
    "description": "Спасибо за поддержку проекта!",
    "payload": "donate_1_star",
    "thanks_text": "🙏 Спасибо за поддержку! Это очень много значит для меня!",
}


def create_donate_price() -> list:
    return [LabeledPrice(label="Поблагодарить", amount=DONATE_STARS)]


async def send_donate_invoice(bot: Bot, chat_id: int) -> bool:
    try:
        await bot.send_invoice(
            chat_id=chat_id,
            title=DONATE_INFO["title"],
            description=DONATE_INFO["description"],
            payload=DONATE_INFO["payload"],
            provider_token="",
            currency=XTR_CURRENCY,
            prices=create_donate_price(),
        )
        return True
    except Exception as e:
        logger.warning(f"Ошибка инвойса: {e}")
        return False


def create_donate_keyboard(persona: str = "normal"):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from services.persona_service import get_donate_button_text

    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text=get_donate_button_text(persona), callback_data="donate_1"),
        ]]
    )
