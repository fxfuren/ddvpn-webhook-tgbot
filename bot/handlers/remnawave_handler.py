from aiohttp import web
import json
import logging
from pathlib import Path
import yaml

from ..utils.config import settings
from ..utils.logger import logger
from ..utils.verify_signature import verify_remnawave_signature
from aiogram import Bot

bot = Bot(token=settings.telegram_bot_token)

# Загружаем список разрешённых событий из YAML
CONFIG_PATH = Path(__file__).parent.parent / "config" / "events.yaml"
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    events_config = yaml.safe_load(f)

ALLOWED_EVENTS = set(events_config.get("remnawave", {}).get("allowed_events", []))
MAX_TELEGRAM_LENGTH = 4000  # ограничение на длину сообщения для Telegram

async def handle_remnawave_webhook(request: web.Request) -> web.Response:
    raw_body = await request.text()
    signature = request.headers.get("X-Remnawave-Signature", "")

    # Проверка подписи
    if not verify_remnawave_signature(raw_body, signature, settings.remnawave_webhook_secret):
        logger.warning("Remnawave webhook rejected: invalid signature")
        return web.Response(status=403, text="Invalid signature")

    # Парсим JSON после проверки подписи
    try:
        body = json.loads(raw_body)
    except Exception:
        body = {"raw": raw_body}

    event = body.get("event", "unknown")
    if event not in ALLOWED_EVENTS:
        logger.info(f"Ignored event: {event}")
        return web.Response(text="Ignored", status=200)

    # Превращаем payload в красивый JSON для Telegram
    data_pretty = json.dumps(body.get("data", {}), indent=2)
    if len(data_pretty) > MAX_TELEGRAM_LENGTH:
        data_pretty = data_pretty[:MAX_TELEGRAM_LENGTH] + "\n...truncated..."

    # Отправляем сообщение в Telegram
    await bot.send_message(
        settings.telegram_chat_id,
        f"🔔 <b>Remnawave Event:</b> <code>{event}</code>\n\n<pre>{data_pretty}</pre>",
        parse_mode="HTML"
    )

    logger.info(f"Remnawave webhook processed: {event}")
    return web.Response(text="OK", status=200)
