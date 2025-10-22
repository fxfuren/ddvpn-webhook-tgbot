from aiohttp import web
from aiogram import Bot
import json
from ..utils.config import settings
from ..utils.logger import logger

async def handle_stripe_webhook(request: web.Request) -> web.Response:
    bot = Bot(token=settings.telegram_bot_token)
    try:
        data = await request.json()
    except Exception:
        text_body = await request.text()
        data = {"raw": text_body}

    event_type = data.get("type", "unknown")

    await bot.send_message(
        settings.telegram_chat_id,
        f"💳 <b>Stripe Event:</b> {event_type}\n<pre>{json.dumps(data, indent=2)}</pre>",
        parse_mode="HTML"
    )

    logger.info(f"Stripe webhook processed: {event_type}")
    return web.Response(text="OK", status=200)
