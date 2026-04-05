import json
import logging
import os
from pathlib import Path
from typing import Optional

from models.user import User

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_FILE = DATA_DIR / "users.json"

# Создаём папку data если её нет
DATA_DIR.mkdir(exist_ok=True)


def load_users() -> dict:
    """Загрузить всех пользователей из JSON"""
    if not DATA_FILE.exists():
        return {}

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Ошибка загрузки данных пользователей: {e}")
        return {}


def save_users(users_data: dict):
    """Сохранить всех пользователей в JSON"""
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(users_data, f, ensure_ascii=False, indent=2)
    except IOError as e:
        logger.error(f"Ошибка сохранения данных пользователей: {e}")


def get_user(telegram_id: int) -> Optional[User]:
    """Получить пользователя по telegram_id"""
    users_data = load_users()
    user_str = users_data.get(str(telegram_id))

    if not user_str:
        return None

    return User(**user_str)


def create_user(telegram_id: int) -> User:
    """Создать нового пользователя"""
    user = User(telegram_id=telegram_id)
    _save_user(user)
    return user


def update_user(user: User):
    """Обновить данные пользователя"""
    _save_user(user)


def _save_user(user: User):
    """Сохранить одного пользователя"""
    users_data = load_users()
    users_data[str(user.telegram_id)] = {
        "telegram_id": user.telegram_id,
        "zodiac_sign": user.zodiac_sign,
        "cities": user.cities,
        "horoscope_persona": getattr(user, "horoscope_persona", "normal"),
    }
    save_users(users_data)


def get_all_users() -> list[User]:
    """Получить всех пользователей"""
    users_data = load_users()
    users = []

    for user_id, user_str in users_data.items():
        users.append(User(**user_str))

    return users
