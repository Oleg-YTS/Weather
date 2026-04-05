import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from services.user_data_service import get_user, update_user
from services.persona_service import get_persona_list, get_persona

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data == "show_persona")
async def callback_show_persona(callback: CallbackQuery):
    """Показать выбор персоны через callback"""
    user = get_user(callback.from_user.id)
    if not user:
        await callback.answer("❌ Пользователь не найден!", show_alert=True)
        return

    personas = get_persona_list()
    current_persona = getattr(user, "horoscope_persona", "normal")

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{'✅ ' if p['id'] == current_persona else ''}{p['name']}",
                    callback_data=f"set_persona_{p['id']}",
                )
            ]
            for p in personas
        ]
    )

    persona_names = "\n".join(
        f"  {'◀' if p['id'] == current_persona else ' '} {p['name']} — {p['description']}"
        for p in personas
    )

    await callback.message.edit_text(
        f"🎭 **Выбери персону гороскопа**\n\n"
        f"{persona_names}\n\n"
        f"Текущая: **{get_persona(current_persona)['name']}**",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )
    await callback.answer()


@router.message(F.text == "/persona")
async def cmd_persona(message):
    """Показать выбор персоны гороскопа"""
    user = get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Пользователь не найден. Отправьте /start")
        return

    personas = get_persona_list()
    current_persona = getattr(user, "horoscope_persona", "normal")

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{'✅ ' if p['id'] == current_persona else ''}{p['name']}",
                    callback_data=f"set_persona_{p['id']}",
                )
            ]
            for p in personas
        ]
    )

    persona_names = "\n".join(
        f"  {'◀' if p['id'] == current_persona else ' '} {p['name']} — {p['description']}"
        for p in personas
    )

    await message.answer(
        f"🎭 **Выбери персону гороскопа**\n\n"
        f"{persona_names}\n\n"
        f"Текущая: **{get_persona(current_persona)['name']}**",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


@router.callback_query(F.data.startswith("set_persona_"))
async def callback_set_persona(callback: CallbackQuery):
    """Установить выбранную персону"""
    persona_id = callback.data.replace("set_persona_", "")
    persona = get_persona(persona_id)

    if not persona:
        await callback.answer("❌ Неизвестная персона!", show_alert=True)
        return

    user = get_user(callback.from_user.id)
    if not user:
        await callback.answer("❌ Пользователь не найден!", show_alert=True)
        return

    old_persona = getattr(user, "horoscope_persona", "normal")
    user.horoscope_persona = persona_id
    update_user(user)

    logger.info(f"Пользователь {callback.from_user.id} сменил персону: {old_persona} → {persona_id}")

    # Очистим кэш при смене персоны, чтобы перегенерировать
    try:
        import json
        from pathlib import Path
        from datetime import date

        cache_file = Path(__file__).parent.parent / "data" / "horoscope_cache.json"
        if cache_file.exists():
            with open(cache_file, "r", encoding="utf-8") as f:
                cache = json.load(f)
            # Удаляем старый кэш пользователя для этой персоны
            keys_to_delete = [k for k in cache if k.startswith(user.zodiac_sign)]
            for k in keys_to_delete:
                del cache[k]
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"Не удалось очистить кэш при смене персоны: {e}")

    await callback.answer(f"✅ Персона изменена на {persona['name']}!", show_alert=True)

    # Покажем результат
    from services.horoscope_service import get_horoscope
    horoscope = get_horoscope(user.zodiac_sign, persona_id)

    if horoscope:
        await callback.message.answer(
            f"🎭 Персона: **{persona['name']}**\n\n" + horoscope,
            parse_mode="Markdown",
        )
    else:
        await callback.message.answer(
            f"✅ Персона изменена на {persona['name']}!\n\n"
            f"Гороскоп придёт в следующей рассылке."
        )
