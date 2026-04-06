import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery, PreCheckoutQuery

from services.donate_service import send_donate_invoice, DONATE_INFO, DONATE_STARS

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "donate_1")
async def cb_donate(callback: CallbackQuery):
    logger.info(f"Донат: пользователь {callback.from_user.id}")
    await callback.answer()
    ok = await send_donate_invoice(callback.message.bot, callback.from_user.id)
    if not ok:
        await callback.message.answer("😔 Не удалось создать платёж. Попробуйте позже.")


@router.pre_checkout_query()
async def pre_checkout(pc: PreCheckoutQuery):
    await pc.answer(ok=True)


@router.message(F.successful_payment)
async def on_pay(message):
    logger.info(f"✅ Донат от {message.from_user.id}")
    await message.answer(DONATE_INFO["thanks_text"])
