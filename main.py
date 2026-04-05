import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

from handlers.setup_handler import router as setup_router
from handlers.persona_handler import router as persona_router
from handlers.donate_handler import router as donate_router
from handlers.admin_handler import router as admin_router, set_scheduler
from handlers.fallback_handler import router as fallback_router
from scheduler import create_scheduler

# Загруем переменные окружения
load_dotenv()

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log", encoding="utf-8"),
    ],
)

logger = logging.getLogger(__name__)


async def on_startup(bot: Bot):
    """Установка webhook при запуске"""
    webhook_url = os.getenv("RENDER_EXTERNAL_URL")
    if webhook_url:
        webhook_path = os.getenv("WEBHOOK_PATH", "/webhook")
        secret_token = os.getenv("WEBHOOK_SECRET", "")
        await bot.set_webhook(
            url=f"{webhook_url}{webhook_path}",
            secret_token=secret_token if secret_token else None,
        )
        logger.info(f"Webhook установлен: {webhook_url}{webhook_path}")


async def on_shutdown(bot: Bot):
    """Удаление webhook при остановке"""
    await bot.delete_webhook()
    logger.info("Webhook удалён")


async def main_polling():
    """Запуск в режиме polling (локальная разработка)"""
    logger.info("Запуск в режиме POLLING...")

    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        logger.error("BOT_TOKEN не установлен в .env файле!")
        return

    bot = Bot(token=bot_token)

    try:
        me = await bot.get_me()
        logger.info(f"Подключение OK! Бот: @{me.username}")
    except Exception as e:
        logger.error(f"Не удалось подключиться к Telegram API: {e}")
        return

    await bot.delete_webhook()

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    await bot.set_my_commands([
        types.BotCommand(command="start", description="Запустить бота"),
        types.BotCommand(command="test", description="Тестовая рассылка"),
        types.BotCommand(command="status", description="Статус планировщика"),
    ])

    dp.include_router(setup_router)
    dp.include_router(persona_router)
    dp.include_router(donate_router)
    dp.include_router(admin_router)
    dp.include_router(fallback_router)

    scheduler = create_scheduler(bot)
    set_scheduler(scheduler)
    scheduler.start()

    try:
        logger.info("Бот запущен в режиме POLLING!")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка: {e}")
    finally:
        scheduler.shutdown()
        await bot.session.close()
        logger.info("Бот остановлен")


async def main_webhook():
    """Запуск в режиме webhook (Render.com)"""
    from aiohttp import web
    from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

    logger.info("Запуск в режиме WEBHOOK...")

    bot_token = os.getenv("BOT_TOKEN")
    webhook_path = os.getenv("WEBHOOK_PATH", "/webhook")
    webhook_secret = os.getenv("WEBHOOK_SECRET", "")

    if not bot_token:
        logger.error("BOT_TOKEN не установлен!")
        return

    bot = Bot(token=bot_token)

    try:
        me = await bot.get_me()
        logger.info(f"Бот: @{me.username}")
    except Exception as e:
        logger.error(f"Не удалось подключиться: {e}")
        return

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    await bot.set_my_commands([
        types.BotCommand(command="start", description="Запустить бота"),
        types.BotCommand(command="test", description="Тестовая рассылка"),
        types.BotCommand(command="status", description="Статус планировщика"),
    ])

    dp.include_router(setup_router)
    dp.include_router(persona_router)
    dp.include_router(donate_router)
    dp.include_router(admin_router)
    dp.include_router(fallback_router)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    scheduler = create_scheduler(bot)
    set_scheduler(scheduler)

    app = web.Application()

    # Health check для Render
    async def health_check(request):
        return web.Response(text="OK", status=200)

    app.router.add_get("/health", health_check)
    app.router.add_get("/", health_check)

    # Webhook handler
    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=webhook_secret if webhook_secret else None,
    ).register(app, path=webhook_path)

    setup_application(app, dp, bot=bot)

    PORT = int(os.getenv("PORT", 10000))
    scheduler.start()

    try:
        logger.info(f"Бот запущен в режиме WEBHOOK на порту {PORT}!")
        web.run_app(app, host="0.0.0.0", port=PORT)
    except Exception as e:
        logger.error(f"Ошибка: {e}")
    finally:
        scheduler.shutdown()
        await bot.session.close()
        logger.info("Бот остановлен")


if __name__ == "__main__":
    # Определяем режим: webhook если RENDER=true, иначе polling
    use_webhook = os.getenv("RENDER", "").lower() == "true"

    if use_webhook:
        asyncio.run(main_webhook())
    else:
        try:
            asyncio.run(main_polling())
        except KeyboardInterrupt:
            logger.info("Бот остановлен пользователем")
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}")
