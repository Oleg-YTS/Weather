from dataclasses import dataclass, field


@dataclass
class User:
    telegram_id: int
    zodiac_sign: str = ""
    cities: list[str] = field(default_factory=list)
    horoscope_persona: str = "normal"

    def has_settings(self) -> bool:
        return bool(self.zodiac_sign and self.cities)

    def add_city(self, city: str) -> bool:
        if city not in self.cities and len(self.cities) < 4:
            self.cities.append(city)
            return True
        return False

    def remove_city(self, city: str) -> bool:
        if city in self.cities:
            self.cities.remove(city)
            return True
        return False
