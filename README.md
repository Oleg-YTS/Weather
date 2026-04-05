# 🌤️ Telegram Bot: Погода и Гороскоп

Бот, который каждое утро в 8:00 присылает прогноз погоды и гороскоп.

## 📋 Возможности

- ✅ Прогноз погоды через OpenWeatherMap API
- ✅ Гороскоп на день через AI (Groq/DeepSeek)
- ✅ До 4 избранных городов на пользователя
- ✅ Выбор знака зодиака с красивыми эмодзи
- ✅ Автоматическая утренняя рассылка в 8:00
- ✅ Inline-кнопки для управления
- ✅ Хранение данных в JSON
- ✅ Простой донат — кнопка «Поблагодарить» за 1 звезду
- ✅ Деплой на Render.com (webhook) или локально (polling)

## 🚀 Установка и запуск

### Локальный запуск (polling)

```bash
pip install -r requirements.txt
python main.py
```

### Деплой на Render.com (webhook)

1. **Создайте репозиторий на GitHub** и запушьте код:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-repo-url>
   git push -u origin main
   ```

2. **Зарегистрируйтесь на [Render.com](https://render.com)**

3. **Создайте Web Service:**
   - Нажмите **New → Web Service**
   - Подключите ваш GitHub репозиторий
   - Render автоматически найдёт `render.yaml` и настроит сервис

4. **Заполните переменные окружения** в панели Render:
   - `BOT_TOKEN` — токен от @BotFather
   - `OPENWEATHER_API_KEY` — ключ OpenWeatherMap
   - `GROQ_API_KEY` — ключ Groq (бесплатный, https://console.groq.com/)
   - `DEEPSEEK_API_KEY` — ключ DeepSeek (опционально, fallback)
   - `WEBHOOK_SECRET` — сгенерируется автоматически

5. **Дождитесь деплоя** — Render автоматически:
   - Установит зависимости из `requirements.txt`
   - Запустит `python main.py`
   - Установит webhook на `https://your-app.onrender.com/webhook`

6. **Проверьте health check:** откройте `https://your-app.onrender.com/health` — должно быть `OK`

> ⚠️ **Важно:** На бесплатном тарифе Render «засыпает» через 15 минут без трафика.
> Для работы планировщика (утренняя рассылка) используйте UptimeRobot для пинга
> эндпоинта `/health` каждые 5 минут, либо перейдите на платный тариф ($7/мес).

## 📁 Структура проекта

```
tg-bot/
├── main.py                     # Точка входа (polling/webhook авто)
├── scheduler.py                # Планировщик задач
├── render.yaml                 # Конфигурация Render.com
├── Procfile                    # Команда запуска для Render
├── requirements.txt            # Зависимости
├── .env                        # Переменные окружения (локально)
├── .env.example                # Пример .env
│
├── models/
│   └── user.py                 # Модель пользователя
│
├── handlers/
│   ├── setup_handler.py        # /start, настройка зодиака и городов
│   ├── persona_handler.py      # Выбор персоны гороскопа
│   ├── donate_handler.py       # Донат (1 звезда)
│   ├── admin_handler.py        # /test, /status
│   ├── fallback_handler.py     # Неизвестные команды
│   └── main_menu_handler.py    # Утилиты главного меню
│
├── services/
│   ├── weather_service.py      # Сервис погоды
│   ├── horoscope_service.py    # Сервис гороскопов (Groq/DeepSeek)
│   ├── persona_service.py      # Персоны гороскопов
│   ├── donate_service.py       # Сервис донатов
│   └── user_data_service.py    # Работа с данными
│
└── data/
    ├── users.json              # Данные пользователей
    └── horoscope_cache.json    # Кэш гороскопов
```

## 🎮 Использование

### Команды

- `/start` - Начать работу с ботом

### Настройка

1. Отправьте `/start`
2. Выберите свой знак зодиака из списка
3. Введите название города

### Управление городами

- **➕ Добавить город** - ввести название нового города
- **➖ Удалить город** - выбрать город из списка

## ⚙️ Настройка расписания

В файле `scheduler.py` можно изменить время рассылки:

```python
scheduler.add_job(
    send_morning_update,
    CronTrigger(hour=8, minute=0, timezone=TIMEZONE),  # Изменить здесь
    ...
)
```

## 🔧 Режимы работы

### Разработка (локально)

```bash
python main.py
```

### Продакшен

Для продакшена рекомендуется:
- Использовать вебхуки вместо поллинга
- Развернуть на VPS или облачном хостинге
- Настроить логирование в файл

## 📝 Логирование

Бот использует базовое логирование в консоль. Для продакшена рекомендуется добавить запись в файл.

## ⚠️ Важно

- Не передавайте `.env` файл в публичный репозиторий
- API ключи должны храниться в секрете
- Бесплатный тариф OpenWeatherMap ограничен 60 запросами/мин

## 🛠️ Технологии

- **Python 3.10+**
- **aiogram 3.x** - Telegram Bot Framework
- **APScheduler** - Планировщик задач
- **requests** - HTTP запросы к API
- **python-dotenv** - Загрузка переменных окружения

## 📞 Поддержка

При возникновении проблем проверьте:
1. Правильность API ключей
2. Подключение к интернету
3. Логи на наличие ошибок

## 📄 Лицензия

MIT
