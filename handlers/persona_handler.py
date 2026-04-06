import logging
import json
from pathlib import Path
from datetime import date

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from services.user_data_service import get_user, update_user
from services.persona_service import get_persona_list, get_persona
from services.horoscope_service import get_horoscope

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "show_persona")
async def cb_show_persona(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    if not user:
        await callback.answer("❌ Не найден!", show_alert=True)
        return

    current = user.horoscope_persona
    personas = get_persona_list()

    kb = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text=f"{'✅ ' if p['id'] == current else ''}{p['name']}",
                callback_data=f"set_persona_{p['id']}",
            )
        ] for p in personas]
    )

    names = "\n".join(f"  {'◀' if p['id'] == current else ' '} {p['name']} — {p['description']}" for p in personas)

    await callback.message.edit_text(
        f"🎭 **Выбери персону**\n\n{names}\n\nТекущая: **{get_persona(current)['name']}**",
        reply_markup=kb,
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set_persona_"))
async def cb_set_persona(callback: CallbackQuery):
    persona_id = callback.data.replace("set_persona_", "")
    persona = get_persona(persona_id)
    if not persona:
        await callback.answer("❌ Неизвестная персона!", show_alert=True)
        return

    user = get_user(callback.from_user.id)
    if not user:
        await callback.answer("❌ Не найден!", show_alert=True)
        return

    user.horoscope_persona = persona_id
    update_user(user)
    logger.info(f"Пользователь {callback.from_user.id} → персона {persona_id}")

    # Очистка кэша
    cache_file = Path(__file__).parent.parent / "data" / "horoscope_cache.json"
    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cache = json.load(f)
            for k in list(cache.keys()):
                if k.startswith(user.zodiac_sign):
                    del cache[k]
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Не удалось очистить кэш: {e}")

    h = get_horoscope(user.zodiac_sign, persona_id)
    if h:
        await callback.message.answer(f"🎭 **{persona['name']}**\n\n{h}", parse_mode="Markdown")
    else:
        await callback.message.answer(f"✅ Персона: {persona['name']}")
    await callback.answer(f"✅ {persona['name']}!", show_alert=True)


@router.message(Command("persona"))
async def cmd_persona(message):
    user = get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Отправьте /start")
        return
    current = user.horoscope_persona
    personas = get_persona_list()
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text=f"{'✅ ' if p['id'] == current else ''}{p['name']}",
                callback_data=f"set_persona_{p['id']}",
            )
        ] for p in personas]
    )
    names = "\n".join(f"  {'◀' if p['id'] == current else ' '} {p['name']} — {p['description']}" for p in personas)
    await message.answer(
        f"🎭 **Выбери персону**\n\n{names}\n\nТекущая: **{get_persona(current)['name']}**",
        reply_markup=kb,
        parse_mode="Markdown",
    )
