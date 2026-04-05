import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart

from services.user_data_service import get_user, create_user, update_user
from services.horoscope_service import get_zodiac_keyboard
from handlers.main_menu_handler import show_main_menu

logger = logging.getLogger(__name__)

router = Router()


class SetupState(StatesGroup):
    """Состояния для настройки пользователя"""
    waiting_for_zodiac = State()
    waiting_for_city = State()


@router.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext):
    """Обработка команды /start"""
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "Пользователь"

    logger.info(f"Пользователь {user_id} запустил команду /start")

    await state.clear()

    user = create_user(user_id)

    # Если всё настроено — сразу меню
    if user.has_settings():
        await show_main_menu(message, user)
        return

    # Если уже есть знак зодиака, просим город
    if user.zodiac_sign:
        await state.set_state(SetupState.waiting_for_city)
        keyboard = _create_city_keyboard(user)
        await message.answer(
            "🏙️ **Управление городами**\n\n"
            f"Уже выбран знак: {user.zodiac_sign}\n\n"
            f"Добавь город кнопкой ниже:",
            reply_markup=keyboard,
            parse_mode="Markdown",
        )
        return

    # Если уже есть города, просим знак зодиака
    if user.cities:
        await state.set_state(SetupState.waiting_for_zodiac)
        keyboard = _create_zodiac_keyboard()
        await message.answer(
            f"♈ **Выбери свой знак зодиака:**",
            reply_markup=keyboard,
        )
        return

    # Настройка с нуля
    welcome_text = (
        f"👋 Привет, {first_name}!\n\n"
        f"Я бот погоды и гороскопов! 🌤️♈\n"
        f"Каждое утро в 8:00 я буду присылать тебе:\n"
        f"• Прогноз погоды для твоих городов\n"
        f"• Гороскоп на день\n\n"
        f"Давай настроим! Выбери свой знак зодиака:"
    )

    await state.set_state(SetupState.waiting_for_zodiac)
    await message.answer(welcome_text, reply_markup=_create_zodiac_keyboard())


@router.message(SetupState.waiting_for_zodiac)
async def process_zodiac_selection(message: Message, state: FSMContext):
    """Обработка выбора знака зодиака (если вдруг через текст)"""
    zodiac_sign = message.text.strip()
    zodiac_signs = get_zodiac_keyboard()

    if zodiac_sign not in zodiac_signs:
        await message.answer("❌ Пожалуйста, выбери знак зодиака из кнопок ниже:")
        return

    await _save_zodiac_and_ask_city(message.from_user.id, zodiac_sign, state, message)


@router.callback_query(F.data.startswith("set_zodiac_"))
async def callback_zodiac_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора знака зодиака через inline-кнопки"""
    zodiac_sign = callback.data.replace("set_zodiac_", "")

    await _save_zodiac_and_ask_city(callback.from_user.id, zodiac_sign, state, callback)
    await callback.answer()


async def _save_zodiac_and_ask_city(user_id: int, zodiac_sign: str, state: FSMContext, source):
    """Сохранить знак зодиака и запросить город"""
    user = get_user(user_id)
    if not user:
        user = create_user(user_id)

    user.zodiac_sign = zodiac_sign
    update_user(user)

    logger.info(f"Пользователь {user_id} выбрал знак зодиака: {zodiac_sign}")

    await state.set_state(SetupState.waiting_for_city)

    keyboard = _create_city_keyboard(user)

    text = (
        f"✅ Знак зодиака {zodiac_sign} сохранён!\n\n"
        f"🏙️ **Управление городами**\n\n"
        f"Добавь город кнопкой ниже:"
    )

    # Если это callback — редактируем сообщение, иначе отправляем новое
    if hasattr(source, 'message') and source.message:
        await source.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await source.answer(text, reply_markup=keyboard, parse_mode="Markdown")


@router.message(SetupState.waiting_for_city)
async def process_city_input(message: Message, state: FSMContext):
    """Обработка ввода города (через чат)"""
    city = message.text.strip()

    if not city:
        await message.answer("❌ Пожалуйста, введи название города:")
        return

    user = get_user(message.from_user.id)
    if not user:
        return

    if city in user.cities:
        await message.answer(f"❌ Город {city} уже в списке!")
        return

    if len(user.cities) >= 4:
        await message.answer(
            "❌ Максимум 4 города. Удалите один, чтобы добавить новый:"
        )
        return

    user.cities.append(city)
    update_user(user)

    logger.info(f"Пользователь {message.from_user.id} добавил город {city}")

    keyboard = _create_city_keyboard(user)

    await message.answer(
        f"✅ Город **{city}** добавлен!",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


@router.callback_query(F.data == "add_city")
async def callback_add_city(callback: CallbackQuery, state: FSMContext):
    """Обработка кнопки добавления города"""
    user = get_user(callback.from_user.id)
    if not user:
        await callback.answer("Пользователь не найден!", show_alert=True)
        return

    if len(user.cities) >= 4:
        await callback.answer("Максимум 4 города!", show_alert=True)
        return

    await state.set_state(SetupState.waiting_for_city)

    await callback.message.edit_text(
        "🏙️ **Введи название города:**\n"
        "Просто напиши название города в чат.",
        reply_markup=None,
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == "remove_city")
async def callback_remove_city(callback: CallbackQuery, state: FSMContext):
    """Обработка кнопки удаления города из главного меню"""
    user = get_user(callback.from_user.id)
    if not user or not user.cities:
        await callback.answer("У тебя нет городов для удаления!", show_alert=True)
        return

    # Создаём inline-клавиатуру с городами пользователя
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"❌ {city}", callback_data=f"del_city_{city}")]
            for city in user.cities
        ]
    )

    await callback.message.edit_text(
        "Выбери город для удаления:",
        reply_markup=keyboard,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("del_city_"))
async def callback_delete_city_confirm(callback: CallbackQuery, state: FSMContext):
    """Удаление выбранного города"""
    city = callback.data.replace("del_city_", "")
    user = get_user(callback.from_user.id)

    if not user:
        await callback.answer("Пользователь не найден!", show_alert=True)
        return

    success = user.remove_city(city)

    if success:
        update_user(user)
        logger.info(f"Пользователь {callback.from_user.id} удалил город {city}")

        await callback.answer(f"✅ Город {city} удалён!", show_alert=True)

        # Если есть ещё города, показываем главное меню
        if user.cities:
            await show_main_menu(callback.message, user)
        else:
            await callback.message.edit_text(
                f"❌ Все города удалены. Добавь новый город:\n"
                f"Введи название города:"
            )
            await state.set_state(SetupState.waiting_for_city)
    else:
        await callback.answer(f"❌ Не удалось удалить город {city}", show_alert=True)


@router.callback_query(F.data == "done_cities")
async def callback_done_cities(callback: CallbackQuery, state: FSMContext):
    """Завершение настройки городов"""
    user = get_user(callback.from_user.id)
    if not user:
        await callback.answer("Пользователь не найден!", show_alert=True)
        return

    if not user.cities:
        await callback.answer("Добавь хотя бы один город!", show_alert=True)
        return

    if not user.zodiac_sign:
        await callback.answer("Выбери знак зодиака!", show_alert=True)
        return

    await state.clear()
    await show_main_menu(callback.message, user)
    await callback.answer()


def _create_city_keyboard(user) -> InlineKeyboardMarkup:
    """Создать клавиатуру для управления городами"""
    buttons = []

    # Показываем уже добавленные города с крестиками
    for city in user.cities:
        buttons.append([
            InlineKeyboardButton(
                text=f"🏙️ {city}",
                callback_data=f"noop_{city}",
            ),
            InlineKeyboardButton(
                text="❌",
                callback_data=f"del_city_{city}",
            ),
        ])

    # Кнопка добавить город
    if len(user.cities) < 4:
        buttons.append([
            InlineKeyboardButton(
                text="➕ Добавить город",
                callback_data="add_city",
            )
        ])

    # Кнопка "Готово" если есть хотя бы один город и знак зодиака
    if user.cities and user.zodiac_sign:
        buttons.append([
            InlineKeyboardButton(
                text="✅ Готово — показать прогноз",
                callback_data="done_cities",
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _create_zodiac_keyboard() -> InlineKeyboardMarkup:
    """Создать inline-клавиатуру с знаками зодиака"""
    zodiac_signs = get_zodiac_keyboard()

    buttons = []
    for i in range(0, len(zodiac_signs), 2):
        row = []
        for sign in zodiac_signs[i:i+2]:
            row.append(InlineKeyboardButton(text=sign, callback_data=f"set_zodiac_{sign}"))
        buttons.append(row)

    return InlineKeyboardMarkup(inline_keyboard=buttons)
