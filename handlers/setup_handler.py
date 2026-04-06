import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart

from services.user_data_service import get_user, create_user, update_user
from services.horoscope_service import get_zodiac_keyboard
from services.weather_service import get_weather
from services.horoscope_service import get_horoscope

logger = logging.getLogger(__name__)

router = Router()


class SetupState(StatesGroup):
    waiting_for_zodiac = State()
    waiting_for_city = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = create_user(message.from_user.id)

    if user.has_settings():
        await _show_menu(message, user)
        return

    if user.zodiac_sign:
        await state.set_state(SetupState.waiting_for_city)
        await message.answer(
            f"🏙️ Знак: {user.zodiac_sign}\n\nДобавь город кнопкой:",
            reply_markup=_city_keyboard(user),
            parse_mode="Markdown",
        )
        return

    if user.cities:
        await state.set_state(SetupState.waiting_for_zodiac)
        await message.answer("♈ Выбери знак зодиака:", reply_markup=_zodiac_keyboard())
        return

    name = message.from_user.first_name or "друг"
    await state.set_state(SetupState.waiting_for_zodiac)
    await message.answer(
        f"👋 Привет, {name}!\n\n"
        f"Я бот погоды и гороскопов! 🌤️\n"
        f"Каждое утро в 8:00 пришлю:\n"
        f"• Прогноз для твоих городов\n"
        f"• Гороскоп на день\n\n"
        f"Выбери знак зодиака:",
        reply_markup=_zodiac_keyboard(),
    )


@router.message(SetupState.waiting_for_zodiac)
async def handle_zodiac_text(message: Message, state: FSMContext):
    signs = get_zodiac_keyboard()
    text = message.text.strip()
    if text not in signs:
        await message.answer("❌ Выбери знак из кнопок:")
        return
    await _save_zodiac(message.from_user.id, text, state, message)


@router.callback_query(F.data.startswith("set_zodiac_"))
async def handle_zodiac_cb(callback: CallbackQuery, state: FSMContext):
    sign = callback.data.replace("set_zodiac_", "")
    await _save_zodiac(callback.from_user.id, sign, state, callback)
    await callback.answer()


async def _save_zodiac(uid: int, sign: str, state: FSMContext, src):
    user = get_user(uid) or create_user(uid)
    user.zodiac_sign = sign
    update_user(user)
    logger.info(f"Пользователь {uid} → {sign}")
    await state.set_state(SetupState.waiting_for_city)
    text = f"✅ {sign} сохранён!\n\n🏙️ Добавь город кнопкой:"
    kb = _city_keyboard(user)
    if hasattr(src, "message") and src.message:
        await src.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    else:
        await src.answer(text, reply_markup=kb, parse_mode="Markdown")


@router.message(SetupState.waiting_for_city)
async def handle_city_text(message: Message, state: FSMContext):
    city = message.text.strip()
    user = get_user(message.from_user.id)
    if not user:
        return
    if city in user.cities:
        await message.answer(f"❌ {city} уже в списке!")
        return
    if len(user.cities) >= 4:
        await message.answer("❌ Максимум 4 города. Удали один:")
        return
    user.cities.append(city)
    update_user(user)
    logger.info(f"Пользователь {message.from_user.id} +{city}")
    await message.answer(f"✅ **{city}** добавлен!", reply_markup=_city_keyboard(user), parse_mode="Markdown")


@router.callback_query(F.data == "add_city")
async def cb_add_city(callback: CallbackQuery, state: FSMContext):
    user = get_user(callback.from_user.id)
    if not user:
        await callback.answer("Пользователь не найден!", show_alert=True)
        return
    if len(user.cities) >= 4:
        await callback.answer("Максимум 4 города!", show_alert=True)
        return
    await state.set_state(SetupState.waiting_for_city)
    await callback.message.edit_text("🏙️ Напиши название города в чат:")
    await callback.answer()


@router.callback_query(F.data == "remove_city")
async def cb_remove_city(callback: CallbackQuery, state: FSMContext):
    user = get_user(callback.from_user.id)
    if not user or not user.cities:
        await callback.answer("Нет городов!", show_alert=True)
        return
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text=f"❌ {c}", callback_data=f"del_city_{c}")
        ] for c in user.cities]
    )
    await callback.message.edit_text("Выбери город для удаления:", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("del_city_"))
async def cb_del_city(callback: CallbackQuery, state: FSMContext):
    city = callback.data.replace("del_city_", "")
    user = get_user(callback.from_user.id)
    if not user:
        await callback.answer("Не найден!", show_alert=True)
        return
    user.remove_city(city)
    update_user(user)
    await callback.answer(f"✅ {city} удалён!", show_alert=True)
    if user.cities:
        await _show_menu(callback.message, user)
    else:
        await callback.message.edit_text("❌ Все города удалены. Введи новый:")
        await state.set_state(SetupState.waiting_for_city)


@router.callback_query(F.data == "done_cities")
async def cb_done(callback: CallbackQuery, state: FSMContext):
    user = get_user(callback.from_user.id)
    if not user or not user.cities or not user.zodiac_sign:
        await callback.answer("Нужен знак и хотя бы 1 город!", show_alert=True)
        return
    await state.clear()
    await _show_menu(callback.message, user)
    await callback.answer()


@router.callback_query(F.data.startswith("noop_"))
async def cb_noop(callback: CallbackQuery):
    await callback.answer()


async def _show_menu(message, user):
    parts = ["🌅 **Прогноз на сегодня**"]
    for c in user.cities:
        w = get_weather(c)
        parts.append(w if w else f"❌ Нет данных для {c}")
    h = get_horoscope(user.zodiac_sign, user.horoscope_persona)
    parts.append(h if h else "❌ Нет гороскопа")

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить город", callback_data="add_city")],
            [InlineKeyboardButton(text="➖ Удалить город", callback_data="remove_city")],
            [InlineKeyboardButton(text="🎭 Персона гороскопа", callback_data="show_persona")],
        ]
    )
    await message.answer("\n\n".join(parts), reply_markup=kb, parse_mode="Markdown")


def _city_keyboard(user) -> InlineKeyboardMarkup:
    btns = []
    for c in user.cities:
        btns.append([
            InlineKeyboardButton(text=f"🏙️ {c}", callback_data=f"noop_{c}"),
            InlineKeyboardButton(text="❌", callback_data=f"del_city_{c}"),
        ])
    if len(user.cities) < 4:
        btns.append([InlineKeyboardButton(text="➕ Добавить город", callback_data="add_city")])
    if user.cities and user.zodiac_sign:
        btns.append([InlineKeyboardButton(text="✅ Готово", callback_data="done_cities")])
    return InlineKeyboardMarkup(inline_keyboard=btns)


def _zodiac_keyboard() -> InlineKeyboardMarkup:
    signs = get_zodiac_keyboard()
    btns = []
    for i in range(0, len(signs), 2):
        row = [InlineKeyboardButton(text=s, callback_data=f"set_zodiac_{s}") for s in signs[i:i+2]]
        btns.append(row)
    return InlineKeyboardMarkup(inline_keyboard=btns)
