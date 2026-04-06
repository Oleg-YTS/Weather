import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

from handlers.setup_handler import router as setup_router
from handlers.persona_handler import router as persona_router
from handlers.donate_handler import router as donate_router
from handlers.admin_handler import router as admin_router, set_scheduler
from handlers.fallback_handler import router as fallback_router
from scheduler import create_scheduler

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot):
    """При старте на Render — регистрируем вебхук в Telegram"""
    external_url = os.getenv("RENDER_EXTERNAL_URL", "").rstrip("/")
    hostname = os.getenv("RENDER_EXTERNAL_HOSTNAME", "")

    if not external_url and hostname:
        external_url = f"https://{hostname}"

    logger.info(f"RENDER_EXTERNAL_URL={os.getenv('RENDER_EXTERNAL_URL')}")
    logger.info(f"RENDER_EXTERNAL_HOSTNAME={hostname}")

    if not external_url:
        logger.error("RENDER_EXTERNAL_URL не установлен! Вебхук не зарегистрирован!")
        return

    path = os.getenv("WEBHOOK_PATH", "/webhook")
    secret = os.getenv("WEBHOOK_SECRET", "")
    # Telegram разрешает только A-Z a-z 0-9 - _
    secret = secret if secret and all(c.isalnum() or c in "-_" for c in secret) else None

    url = f"{external_url}{path}"
    try:
        await bot.set_webhook(url=url, secret_token=secret)
        logger.info(f"✅ Вебхук установлен: {url}")
    except Exception as e:
        logger.error(f"❌ Ошибка установки вебхука: {e}")


async def on_shutdown(bot: Bot):
    """При остановке — НЕ удаляем вебхук (Render перезапускается часто)"""
    pass


def run_polling():
    """Локальный режим — polling"""
    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.error("BOT_TOKEN не установлен!")
        return

    async def _main():
        bot = Bot(token=token)
        try:
            me = await bot.get_me()
            logger.info(f"Подключён: @{me.username}")
        except Exception as e:
            logger.error(f"Нет подключения: {e}")
            return

        await bot.delete_webhook()
        await bot.set_my_commands([
            types.BotCommand(command="start", description="Запустить бота"),
            types.BotCommand(command="test", description="Тестовая рассылка"),
            types.BotCommand(command="status", description="Статус"),
        ])

        dp = Dispatcher(storage=MemoryStorage())
        dp.include_router(setup_router)
        dp.include_router(persona_router)
        dp.include_router(donate_router)
        dp.include_router(admin_router)
        dp.include_router(fallback_router)

        scheduler = create_scheduler(bot)
        set_scheduler(scheduler)
        scheduler.start()

        try:
            logger.info("Бот запущен (polling)!")
            await dp.start_polling(bot)
        except Exception as e:
            logger.error(f"Ошибка: {e}")
        finally:
            scheduler.shutdown()
            await bot.session.close()

    asyncio.run(_main())


def run_webhook():
    """Render.com — webhook + aiohttp сервер"""
    from aiohttp import web
    from aiogram.webhook.aiohttp_server import (
        SimpleRequestHandler,
        setup_application,
    )

    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.error("BOT_TOKEN не установлен!")
        return

    bot = Bot(token=token)

    dp = Dispatcher(storage=MemoryStorage())
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

    # Health check
    async def health(request):
        return web.Response(text="OK", status=200)

    app.router.add_get("/health", health)
    app.router.add_get("/", health)

    # Запуск планировщика когда event loop уже работает
    async def app_startup(app):
        scheduler.start()
        logger.info("Планировщик запущен")

    async def app_shutdown(app):
        scheduler.shutdown()
        await bot.session.close()
        logger.info("Бот остановлен")

    app.on_startup.append(app_startup)
    app.on_shutdown.append(app_shutdown)

    # Обработчик вебхука
    secret = os.getenv("WEBHOOK_SECRET", "")
    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=secret if secret else None,
    ).register(app, path="/webhook")

    setup_application(app, dp, bot=bot)

    port = int(os.getenv("PORT", 10000))
    logger.info(f"Бот запущен (webhook) на порту {port}!")

    web.run_app(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    if os.getenv("RENDER", "").lower() == "true":
        run_webhook()
    else:
        try:
            run_polling()
        except KeyboardInterrupt:
            logger.info("Остановлен")
