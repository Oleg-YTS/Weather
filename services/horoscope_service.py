import logging
import os
import json
from datetime import date
from pathlib import Path

from openai import OpenAI, APIConnectionError, APITimeoutError
from dotenv import load_dotenv

from services.persona_service import get_system_prompt

load_dotenv()

logger = logging.getLogger(__name__)

# Знаки зодиака с эмодзи и английскими названиями
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

# ─── Groq API (ПРИОРИТЕТ) ───
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = None
if GROQ_API_KEY:
    groq_client = OpenAI(
        api_key=GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1",
    )
    logger.info("Groq клиент инициализирован")
else:
    logger.warning("GROQ_API_KEY не установлен")

# ─── DeepSeek API (FALLBACK) ───
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
deepseek_client = None
if DEEPSEEK_API_KEY:
    deepseek_client = OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com",
    )
    logger.info("DeepSeek клиент инициализирован")
else:
    logger.warning("DEEPSEEK_API_KEY не установлен")

# Кэш гороскопов (файл) — кэш теперь с учётом персоны
CACHE_DIR = Path(__file__).parent.parent / "data"
CACHE_FILE = CACHE_DIR / "horoscope_cache.json"
CACHE_DIR.mkdir(exist_ok=True)


# ─── КЭШИРОВАНИЕ ───

def _load_cache() -> dict:
    """Загрузить кэш гороскопов"""
    if not CACHE_FILE.exists():
        return {}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _save_cache(cache: dict):
    """Сохранить кэш гороскопов"""
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except IOError as e:
        logger.error(f"Ошибка сохранения кэша гороскопов: {e}")


def _get_cached_text(zodiac_sign: str, persona: str = "normal") -> str | None:
    """Получить закэшированный текст гороскопа (если он сегодня)"""
    cache = _load_cache()
    # Ключ = знак + персона + дата
    cache_key = f"{zodiac_sign}:{persona}"
    entry = cache.get(cache_key)
    if not entry:
        return None
    
    cached_date = entry.get("date")
    cached_text = entry.get("text")
    
    if cached_date == date.today().isoformat() and cached_text:
        return cached_text
    
    return None


def _save_to_cache(zodiac_sign: str, text: str, persona: str = "normal"):
    """Сохранить гороскоп в кэш с сегодняшней датой"""
    cache = _load_cache()
    cache_key = f"{zodiac_sign}:{persona}"
    cache[cache_key] = {
        "date": date.today().isoformat(),
        "text": text,
        "persona": persona,
    }
    _save_cache(cache)


# ─── AI ГЕНЕРАЦИЯ ───

# Типичные опечатки AI и их исправления
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
}


def _fix_ai_typos(text: str) -> str:
    """Исправить типичные опечатки AI (пропущенные буквы в цензурных словах)"""
    import re
    
    for typo, fix in TYPO_FIXES.items():
        # Заменяем только целые слова (не внутри других слов)
        pattern = r'\b' + re.escape(typo) + r'\b'
        text = re.sub(pattern, fix, text, flags=re.IGNORECASE)
    
    return text


def escape_md_for_telegram(text: str) -> str:
    """Экранировать спецсимволы Markdown для Telegram (чтобы * не ломал парсинг)"""
    # Telegram Markdown спецсимволы: _ * [ ] ( ) ~ ` > # + - = | { } . !
    # В режиме MarkdownV2 все они должны быть экранированы \
    # Но нам нужно сохранить нашу разметку (**жирный**) в сообщениях бота
    # Поэтому экранируем ТОЛЬКО одиночные * внутри слов (цензура)
    
    import re
    # Заменяем * внутри слов (х*й → х\*й)
    text = re.sub(r'(\w)\*(\w)', r'\1\*\2', text)
    
    return text

def _generate_groq_horoscope(zodiac_sign: str, english_name: str, persona: str = "normal") -> str | None:
    """Сгенерировать гороскоп через Groq API"""
    if not groq_client:
        return None

    today = date.today().strftime("%A, %d %B %Y")
    user_prompt = (
        f"Сегодня {today}. Напиши гороскоп для знака зодиака {zodiac_sign} ({english_name}). "
        f"Сделай его уникальным и не похожим на вчерашний."
    )

    system_prompt = get_system_prompt(persona)

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.9,
            max_tokens=200,
            timeout=10,
        )

        text = response.choices[0].message.content.strip()
        
        if text and len(text) > 20:
            text = _fix_ai_typos(text)
            logger.info(f"✅ Гороскоп сгенерирован через Groq (llama-3.3-70b) для {zodiac_sign} [{persona}]")
            return text
        else:
            logger.warning(f"Groq вернул пустой ответ для {zodiac_sign}")
            return None

    except (APIConnectionError, APITimeoutError) as e:
        logger.warning(f"Groq недоступен (connection/timeout): {e}")
        return None
    except Exception as e:
        logger.error(f"Ошибка Groq API: {e}")
        return None


def _generate_deepseek_horoscope(zodiac_sign: str, english_name: str, persona: str = "normal") -> str | None:
    """Сгенерировать гороскоп через DeepSeek API"""
    if not deepseek_client:
        return None

    today = date.today().strftime("%A, %d %B %Y")
    user_prompt = (
        f"Сегодня {today}. Напиши гороскоп для знака зодиака {zodiac_sign} ({english_name}). "
        f"Сделай его уникальным и не похожим на вчерашний."
    )

    system_prompt = get_system_prompt(persona)

    try:
        response = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.9,
            max_tokens=200,
            timeout=15,
        )

        text = response.choices[0].message.content.strip()
        
        if text and len(text) > 20:
            text = _fix_ai_typos(text)
            logger.info(f"✅ Гороскоп сгенерирован через DeepSeek для {zodiac_sign} [{persona}]")
            return text
        else:
            logger.warning(f"DeepSeek вернул пустой ответ для {zodiac_sign}")
            return None

    except (APIConnectionError, APITimeoutError) as e:
        logger.warning(f"DeepSeek недоступен (connection/timeout): {e}")
        return None
    except Exception as e:
        logger.error(f"Ошибка DeepSeek API: {e}")
        return None


# ─── FALLBACK ───

def _get_fallback_horoscope(zodiac_sign: str) -> str:
    """Запасной гороскоп, если все AI недоступны"""
    fallback_data = {
        "♈ Овен": "Сегодня ваша энергия на высоте. Используйте это для решения задач, которые откладывали. Вечером уделите время семье.",
        "♉ Телец": "Финансовый день будет стабильным. Звёзды советуют не торопиться с крупными покупками. Приятный сюрприз ждёт во второй половине дня.",
        "♊ Близнецы": "День общения и новых идей. Возможно интересное знакомство. Не бойтесь делиться планами — вас поддержат.",
        "♋ Рак": "Сосредоточьтесь на домашнем уюте. Мелкие бытовые задачи принесут неожиданное удовлетворение. Вечером — время для творчества.",
        "♌ Лев": "Ваша харизма сегодня особенно сильна. Используйте это для переговоров и важных разговоров. Удачный день для презентаций.",
        "♍ Дева": "Внимание к деталям принесёт плоды. Перепроверьте важные документы. Здоровье требует внимания — прогулка на свежем воздухе будет полезна.",
        "♎ Весы": "День компромиссов и гармонии. Если назрел конфликт — сегодня лучший момент для примирения. Финансовый совет: не давайте в долг.",
        "♏ Скорпион": "Интуиция сегодня особенно остра. Доверяйте своим ощущениям. Возможны неожиданные новости от дальних родственников.",
        "♐ Стрелец": "Хороший день для планирования путешествий или обучения. Откроются новые возможности. Не отказывайтесь от спонтанных приглашений.",
        "♑ Козерог": "Работа сегодня принесёт удовлетворение. Коллеги оценят ваши усилия. Вечером возможно неожиданное романтическое приключение.",
        "♒ Водолей": "Нестандартные идеи сегодня будут особенно удачны. Не бойтесь идти против течения. Друзья удивят интересным предложением.",
        "♓ Рыбы": "Творческая энергия на подъёме. Займитесь хобби или начните изучать что-то новое. Вечером звёзды советуют отдохнуть в тишине.",
    }

    text = fallback_data.get(zodiac_sign, "День благоприятен для новых начинаний. Звёзды советуют быть открытым к возможностям.")

    return f"{zodiac_sign} **Гороскоп на сегодня**\n\n📖 {text}"


# ─── ГЛАВНАЯ ФУНКЦИЯ ───

def get_horoscope(zodiac_sign: str, persona: str = "normal") -> str | None:
    """
    Получить гороскоп на сегодня.

    Приоритет:
    1. Groq API (llama-3.3-70b-versatile) — быстрый, бесплатный
    2. DeepSeek API (deepseek-chat) — fallback если Groq упал
    3. Встроенные заглушки по знаку зодиака
    """
    english_name = ZODIAC_SIGNS.get(zodiac_sign)
    if not english_name:
        logger.error(f"Неизвестный знак зодиака: {zodiac_sign}")
        return None

    # Проверяем кэш (если уже генерировали сегодня для этой персоны)
    cached = _get_cached_text(zodiac_sign, persona)
    if cached:
        logger.info(f"📦 Гороскоп взят из кэша для {zodiac_sign} [{persona}]")
        escaped = escape_md_for_telegram(cached)
        return f"{zodiac_sign} **Гороскоп на сегодня**\n\n📖 {escaped}"

    # 1️⃣ Пробуем Groq
    horoscope_text = _generate_groq_horoscope(zodiac_sign, english_name, persona)

    # 2️⃣ Если Groq упал — пробуем DeepSeek
    if not horoscope_text:
        logger.info(f"Groq недоступен, пробуем DeepSeek для {zodiac_sign} [{persona}]")
        horoscope_text = _generate_deepseek_horoscope(zodiac_sign, english_name, persona)

    # 3️⃣ Если оба AI недоступны — fallback
    if horoscope_text:
        _save_to_cache(zodiac_sign, horoscope_text, persona)
        escaped = escape_md_for_telegram(horoscope_text)
        return f"{zodiac_sign} **Гороскоп на сегодня**\n\n📖 {escaped}"
    
    logger.warning(f"⚠️ AI недоступен, используем fallback для {zodiac_sign} [{persona}]")
    return _get_fallback_horoscope(zodiac_sign)


def get_zodiac_keyboard() -> list:
    """Получить список знаков зодиака для клавиатуры"""
    return list(ZODIAC_SIGNS.keys())
