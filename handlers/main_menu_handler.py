import logging

from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from services.weather_service import get_weather
from services.horoscope_service import get_horoscope

logger = logging.getLogger(__name__)


async def show_main_menu(message: Message, user):
    """Показать главное меню с inline-кнопками"""
    weather_parts = []
    for city in user.cities:
        weather = get_weather(city)
        if weather:
            weather_parts.append(weather)
        else:
            weather_parts.append(f"❌ Не удалось получить погоду для {city}")

    persona = getattr(user, "horoscope_persona", "normal")
    horoscope = get_horoscope(user.zodiac_sign, persona)
    if not horoscope:
        horoscope = f"❌ Не удалось получить гороскоп для {user.zodiac_sign}"

    full_message = "🌅 **Прогноз на сегодня**\n\n"
    full_message += "\n\n".join(weather_parts)
    full_message += "\n\n" + horoscope

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить город", callback_data="add_city")],
            [InlineKeyboardButton(text="➖ Удалить город", callback_data="remove_city")],
            [InlineKeyboardButton(text="🎭 Персона гороскопа", callback_data="show_persona")],
        ]
    )

    await message.answer(full_message, reply_markup=keyboard, parse_mode="Markdown")


async def show_main_menu_edit(callback_query, user):
    """Показать главное меню через редактирование сообщения"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    weather_parts = []
    for city in user.cities:
        weather = get_weather(city)
        if weather:
            weather_parts.append(weather)
        else:
            weather_parts.append(f"❌ Не удалось получить погоду для {city}")

    persona = getattr(user, "horoscope_persona", "normal")
    horoscope = get_horoscope(user.zodiac_sign, persona)
    if not horoscope:
        horoscope = f"❌ Не удалось получить гороскоп для {user.zodiac_sign}"

    full_message = "🌅 **Прогноз на сегодня**\n\n"
    full_message += "\n\n".join(weather_parts)
    full_message += "\n\n" + horoscope

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить город", callback_data="add_city")],
            [InlineKeyboardButton(text="➖ Удалить город", callback_data="remove_city")],
        ]
    )

    await callback_query.message.edit_text(
        full_message,
        reply_markup=keyboard,
        parse_mode="Markdown",
    )
