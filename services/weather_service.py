import logging
import os
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

logger = logging.getLogger(__name__)


def get_weather(city: str) -> str | None:
    """
    Получить текущую погоду для города.
    Возвращает отформатированную строку или None при ошибке.
    """
    if not OPENWEATHER_API_KEY:
        logger.error("OpenWeather API ключ не установлен")
        return None

    params = {
        "q": city,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": "ru",
    }

    try:
        response = requests.get(OPENWEATHER_BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        temp = round(data["main"]["temp"])
        feels_like = round(data["main"]["feels_like"])
        description = data["weather"][0]["description"]
        wind = round(data["wind"]["speed"], 1)
        humidity = data["main"]["humidity"]
        city_name = data["name"]

        # Подбираем эмодзи по описанию погоды
        weather_emoji = _get_weather_emoji(description)

        weather_text = (
            f"{weather_emoji} **{city_name}**\n"
            f"🌡️ Температура: {temp:+}°C (ощущается как {feels_like:+}°C)\n"
            f"📝 {description.capitalize()}\n"
            f"💨 Ветер: {wind} м/с\n"
            f"💧 Влажность: {humidity}%"
        )

        return weather_text

    except requests.exceptions.Timeout:
        logger.error(f"Таймаут запроса погоды для города {city}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка запроса погоды для города {city}: {e}")
        return None
    except KeyError as e:
        logger.error(f"Ошибка парсинга данных погоды для города {city}: {e}")
        return None


def _get_weather_emoji(description: str) -> str:
    """Подобрать эмодзи по описанию погоды"""
    description = description.lower()

    if "ясно" in description or "clear" in description:
        return "☀️"
    elif "облачн" in description or "cloud" in description:
        if "перемен" in description or "partial" in description:
            return "⛅"
        return "☁️"
    elif "дожд" in description or "rain" in description or "drizzle" in description:
        return "🌧️"
    elif "снег" in description or "snow" in description:
        return "❄️"
    elif "гроз" in description or "thunder" in description:
        return "⛈️"
    elif "туман" in description or "fog" in description or "haze" in description:
        return "🌫️"
    else:
        return "🌤️"
