import asyncio
from aiohttp import web
from .utils.logger import setup_logger
from .utils.config import settings
from .handlers.remnawave_handler import handle_remnawave_webhook
from .handlers.alert_handler import handle_alert_webhook
from aiogram import Bot

"""
Главный файл запуска webhook бота.

- Настраивает aiohttp сервер для приёма вебхуков
- Инициализирует Telegram бота через aiogram
- Добавляет маршруты для разных типов вебхуков
- Корректно закрывает сессию бота при завершении
"""

# Настраиваем логирование
logger = setup_logger()

# Создаём экземпляр бота один раз
bot = Bot(token=settings.telegram_bot_token)

if __name__ == "__main__":
    # Создаём aiohttp приложение
    app = web.Application()

    # Роуты для вебхуков
    app.router.add_post("/webhook/remnawave", handle_remnawave_webhook)
    app.router.add_post("/webhook/alert/{token}", handle_alert_webhook)

    try:
        # Логируем старт
        logger.info(f"Webhook bot starting on 0.0.0.0:{settings.bot_internal_port}")
        # Запускаем aiohttp сервер
        web.run_app(app, host="0.0.0.0", port=settings.bot_internal_port)
    finally:
        # Корректное закрытие aiohttp сессии бота после остановки сервера
        asyncio.run(bot.session.close())
        logger.info("Bot session closed")
