import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery, PreCheckoutQuery

from services.donate_service import (
    send_donate_invoice,
    DONATE_INFO,
    DONATE_STARS,
)

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data == "donate_1")
async def callback_donate(callback: CallbackQuery):
    """Обработка кнопки доната"""
    logger.info(f"Пользователь {callback.from_user.id} хочет задонатить {DONATE_STARS} звезду")

    await callback.answer()

    success = await send_donate_invoice(callback.message.bot, callback.from_user.id, DONATE_STARS)

    if not success:
        await callback.message.answer(
            "😔 Упс! Не удалось создать платёж. Попробуйте позже.",
        )


@router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout: PreCheckoutQuery):
    """Подтверждение оплаты (обязательно для Stars)"""
    await pre_checkout.answer(ok=True)


@router.message(F.successful_payment)
async def handle_successful_payment(message):
    """Обработка успешного платежа"""
    logger.info(f"✅ Пользователь {message.from_user.id} задонатил {DONATE_STARS} звезду!")
    await message.answer(DONATE_INFO["thanks_text"])
