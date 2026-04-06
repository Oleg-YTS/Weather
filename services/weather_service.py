import logging
import os

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

logger = logging.getLogger(__name__)


def get_weather(city: str) -> str | None:
    if not API_KEY:
        logger.error("OpenWeather API ключ не установлен")
        return None

    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric",
        "lang": "ru",
    }

    try:
        r = requests.get(BASE_URL, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()

        temp = round(data["main"]["temp"])
        feels = round(data["main"]["feels_like"])
        desc = data["weather"][0]["description"].capitalize()
        wind = round(data["wind"]["speed"], 1)
        humidity = data["main"]["humidity"]
        city_name = data["name"]

        emoji = _emoji(desc)

        return (
            f"{emoji} **{city_name}**\n"
            f"🌡️ {temp:+}°C (ощущается {feels:+}°C)\n"
            f"📝 {desc}\n"
            f"💨 {wind} м/с  💧 {humidity}%"
        )
    except Exception as e:
        logger.error(f"Ошибка погоды для {city}: {e}")
        return None


def _emoji(desc: str) -> str:
    d = desc.lower()
    if "ясно" in d or "clear" in d:
        return "☀️"
    if "облачн" in d or "cloud" in d:
        return "⛅" if "перемен" in d or "partial" in d else "☁️"
    if "дожд" in d or "rain" in d or "drizzle" in d:
        return "🌧️"
    if "снег" in d or "snow" in d:
        return "❄️"
    if "гроз" in d or "thunder" in d:
        return "⛈️"
    if "туман" in d or "fog" in d or "haze" in d:
        return "🌫️"
    return "🌤️"
