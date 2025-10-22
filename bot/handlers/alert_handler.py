from aiohttp import web
from aiogram import Bot
import json
from jinja2 import Template
from pathlib import Path
from ..utils.config import settings
from ..utils.logger import logger

# Инициализация Telegram-бота один раз
bot = Bot(token=settings.telegram_bot_token)

# Путь к шаблону для Alert сообщений
TEMPLATE_PATH = Path(__file__).parent.parent / "templates" / "alert.html"


async def handle_alert_webhook(request: web.Request) -> web.Response:
    """
    Обработчик AlertPayload от Observer.

    Функционал:
    - Проверяет токен прямо в URL для безопасности.
    - Парсит JSON из POST-запроса.
    - Формирует красивое сообщение через Jinja2 шаблон.
    - Отправляет сообщение в Telegram.
    - Логирует результат обработки.

    Параметры:
    request : web.Request
        Объект aiohttp запроса.

    Возвращает:
    web.Response
        HTTP-ответ с кодом 200 (OK) или 403 (Forbidden).
    """

    # Проверка токена из URL для безопасности
    token_in_url = request.match_info.get("token", "")
    if token_in_url != settings.alert_webhook_secret:
        logger.warning("Unauthorized alert webhook request!")
        return web.Response(status=403, text="Forbidden")

    # Пытаемся распарсить JSON тело запроса
    try:
        data = await request.json()
    except Exception:
        # Если JSON некорректен — сохраняем сырой текст
        text_body = await request.text()
        data = {"raw": text_body}
        logger.warning("Received non-JSON alert payload!")

    # Рендерим сообщение через Jinja2 шаблон
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = Template(f.read())

    message_text = template.render(
        user_identifier=data.get("user_identifier", "unknown"),
        detected_ips_count=data.get("detected_ips_count", 0),
        limit=data.get("limit", 0),
        all_user_ips=data.get("all_user_ips", []),
        block_duration=data.get("block_duration", "unknown"),
        violation_type=data.get("violation_type", "unknown")
    )

    # Отправка сформированного сообщения в Telegram
    await bot.send_message(
        settings.telegram_chat_id,
        message_text,
        parse_mode="HTML"
    )

    logger.info(f"Alert webhook processed: user {data.get('user_identifier','unknown')}")
    return web.Response(text="OK", status=200)
