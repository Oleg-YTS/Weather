import json
from pathlib import Path
from typing import Optional

from models.user import User

DATA_FILE = Path(__file__).parent.parent / "data" / "users.json"
DATA_FILE.parent.mkdir(exist_ok=True)


def _load() -> dict:
    if not DATA_FILE.exists():
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _save(data: dict):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_user(telegram_id: int) -> Optional[User]:
    users = _load()
    d = users.get(str(telegram_id))
    return User(**d) if d else None


def create_user(telegram_id: int) -> User:
    user = User(telegram_id=telegram_id)
    _save_user(user)
    return user


def update_user(user: User):
    _save_user(user)


def _save_user(user: User):
    users = _load()
    users[str(user.telegram_id)] = {
        "telegram_id": user.telegram_id,
        "zodiac_sign": user.zodiac_sign,
        "cities": user.cities,
        "horoscope_persona": user.horoscope_persona,
    }
    _save(users)


def get_all_users() -> list[User]:
    users = _load()
    return [User(**v) for v in users.values()]
