import asyncio
from aiohttp import web
from .utils.logger import setup_logger
from .utils.config import settings
from .handlers.remnawave_handler import handle_remnawave_webhook
from .handlers.stripe_handler import handle_stripe_webhook
from aiogram import Bot

logger = setup_logger()

bot = Bot(token=settings.telegram_bot_token)

if __name__ == "__main__":
    app = web.Application()
    app.router.add_post("/webhook/remnawave", handle_remnawave_webhook)
    app.router.add_post("/webhook/stripe", handle_stripe_webhook)

    try:
        logger.info(f"Webhook bot starting on 0.0.0.0:{settings.bot_internal_port}")
        web.run_app(app, host="0.0.0.0", port=settings.bot_internal_port)
    finally:
        # корректное закрытие aiohttp сессии бота
        asyncio.run(bot.session.close())
        logger.info("Bot session closed")
