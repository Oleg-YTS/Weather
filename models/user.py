from dataclasses import dataclass, field
from typing import List


@dataclass
class User:
    """Модель пользователя Telegram"""
    telegram_id: int
    zodiac_sign: str = ""
    cities: List[str] = field(default_factory=list)
    horoscope_persona: str = "normal"

    def has_settings(self) -> bool:
        """Проверка, настроил ли пользователь знак зодиака и города"""
        return bool(self.zodiac_sign and self.cities)

    def add_city(self, city: str) -> bool:
        """Добавить город (максимум 4)"""
        if city not in self.cities and len(self.cities) < 4:
            self.cities.append(city)
            return True
        return False

    def remove_city(self, city: str) -> bool:
        """Удалить город"""
        if city in self.cities:
            self.cities.remove(city)
            return True
        return False
