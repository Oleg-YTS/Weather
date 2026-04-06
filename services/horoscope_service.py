import json
import logging
import os
import re
from datetime import date
from pathlib import Path

from openai import OpenAI
from dotenv import load_dotenv

from services.persona_service import get_system_prompt

load_dotenv()
logger = logging.getLogger(__name__)

ZODIAC_SIGNS = {
    "♈ Овен": "Aries",
    "♉ Телец": "Taurus",
    "♊ Близнецы": "Gemini",
    "♋ Рак": "Cancer",
    "♌ Лев": "Leo",
    "♍ Дева": "Virgo",
    "♎ Весы": "Libra",
    "♏ Скорпион": "Scorpio",
    "♐ Стрелец": "Sagittarius",
    "♑ Козерог": "Capricorn",
    "♒ Водолей": "Aquarius",
    "♓ Рыбы": "Pisces",
}

# Groq (приоритет)
groq_client = None
if os.getenv("GROQ_API_KEY"):
    groq_client = OpenAI(api_key=os.getenv("GROQ_API_KEY"), base_url="https://api.groq.com/openai/v1")

# DeepSeek (fallback)
deepseek_client = None
if os.getenv("DEEPSEEK_API_KEY"):
    deepseek_client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")

# Кэш
CACHE_FILE = Path(__file__).parent.parent / "data" / "horoscope_cache.json"
CACHE_FILE.parent.mkdir(exist_ok=True)

# ─── Исправление опечаток AI ───

TYPO_FIXES = {
    "хй": "х*й",
    "хйом": "х*ём",
    "хйовой": "х*ёвой",
    "хйов": "х*ёв",
    "хйовый": "х*ёвый",
    "хйовая": "х*ёвая",
    "хйовое": "х*ёвое",
    "пздец": "п*здец",
    "пздеца": "п*здеца",
    "блят": "бл*ть",
    "ебан": "ёбан",
    "ебуч": "ёбуч",
    "нах": "на*уй",
    "пид": "п*дор",
    "сука": "с*ка",
    "бля": "бл*ть",
    "блядь": "бл*дь",
    "ппел": "пепел",
    "блть": "бл*ть",
}


def _fix_ai_typos(text: str) -> str:
    """Исправить типичные опечатки AI"""
    for typo, fix in TYPO_FIXES.items():
        pattern = r'\b' + re.escape(typo) + r'\b'
        text = re.sub(pattern, fix, text, flags=re.IGNORECASE)
    return text


def escape_md_for_telegram(text: str) -> str:
    """Экранировать одиночные * внутри слов для Telegram Markdown"""
    return re.sub(r'(\w)\*(\w)', r'\1\*\2', text)


def _load_cache() -> dict:
    if not CACHE_FILE.exists():
        return {}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _save_cache(cache: dict):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def _get_cached(zodiac: str, persona: str) -> str | None:
    entry = _load_cache().get(f"{zodiac}:{persona}")
    if entry and entry.get("date") == date.today().isoformat():
        return entry.get("text")
    return None


def _save_cache_entry(zodiac: str, text: str, persona: str):
    cache = _load_cache()
    cache[f"{zodiac}:{persona}"] = {"date": date.today().isoformat(), "text": text}
    _save_cache(cache)


def _generate(client, model, zodiac: str, english: str, persona: str) -> str | None:
    today = date.today().strftime("%A, %d %B %Y")
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": get_system_prompt(persona)},
                {"role": "user", "content": f"Сегодня {today}. Гороскоп для {zodiac} ({english})."},
            ],
            temperature=0.9,
            max_tokens=200,
            timeout=10,
        )
        text = resp.choices[0].message.content.strip()
        return text if text and len(text) > 20 else None
    except Exception as e:
        logger.warning(f"Ошибка генерации ({model}): {e}")
        return None


FALLBACKS = {
    "♈ Овен": "Сегодня ваша энергия на высоте. Используйте это для решения отложенных задач. Вечером уделите время семье.",
    "♉ Телец": "Финансовый день будет стабильным. Не торопитесь с крупными покупками. Приятный сюрприз ждёт во второй половине дня.",
    "♊ Близнецы": "День общения и новых идей. Возможно интересное знакомство. Не бойтесь делиться планами.",
    "♋ Рак": "Сосредоточьтесь на домашнем уюте. Бытовые задачи принесут удовлетворение. Вечером — время для творчества.",
    "♌ Лев": "Харизма особенно сильна сегодня. Используйте это для переговоров. Удачный день для презентаций.",
    "♍ Дева": "Внимание к деталям принесёт плоды. Перепроверьте документы. Прогулка на свежем воздухе будет полезна.",
    "♎ Весы": "День компромиссов и гармонии. Лучший момент для примирения. Финансовый совет: не давайте в долг.",
    "♏ Скорпион": "Интуиция особенно остра. Доверяйте ощущениям. Возможны неожиданные новости от дальних родственников.",
    "♐ Стрелец": "Хороший день для планирования путешествий или обучения. Откроются новые возможности.",
    "♑ Козерог": "Работа принесёт удовлетворение. Коллеги оценят усилия. Вечером возможно романтическое приключение.",
    "♒ Водолей": "Нестандартные идеи будут особенно удачны. Не бойтесь идти против течения. Друзья удивят предложением.",
    "♓ Рыбы": "Творческая энергия на подъёме. Займитесь хобби. Вечером звёзды советуют отдохнуть в тишине.",
}


def get_horoscope(zodiac: str, persona: str = "normal") -> str:
    english = ZODIAC_SIGNS.get(zodiac)
    if not english:
        return f"❌ Неизвестный знак: {zodiac}"

    cached = _get_cached(zodiac, persona)
    if cached:
        escaped = escape_md_for_telegram(cached)
        return f"{zodiac} **Гороскоп на сегодня**\n\n📖 {escaped}"

    text = None
    if groq_client:
        text = _generate(groq_client, "llama-3.3-70b-versatile", zodiac, english, persona)
    if not text and deepseek_client:
        text = _generate(deepseek_client, "deepseek-chat", zodiac, english, persona)

    if text:
        text = _fix_ai_typos(text)
        _save_cache_entry(zodiac, text, persona)
        escaped = escape_md_for_telegram(text)
        return f"{zodiac} **Гороскоп на сегодня**\n\n📖 {escaped}"

    fallback = FALLBACKS.get(zodiac, "День благоприятен для новых начинаний.")
    return f"{zodiac} **Гороскоп на сегодня**\n\n📖 {fallback}"


def get_zodiac_keyboard() -> list[str]:
    return list(ZODIAC_SIGNS.keys())
