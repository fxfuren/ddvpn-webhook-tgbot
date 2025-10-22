from aiohttp import web
import json
import logging
from pathlib import Path
import yaml
from jinja2 import Template

from ..utils.config import settings
from ..utils.logger import logger
from ..utils.verify_signature import verify_remnawave_signature
from aiogram import Bot

bot = Bot(token=settings.telegram_bot_token)

"""
Загрузка конфигурации разрешённых событий из YAML.
Файл events.yaml содержит список событий, которые мы хотим обрабатывать.
"""
CONFIG_PATH = Path(__file__).parent.parent / "config" / "events.yaml"
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    events_config = yaml.safe_load(f)

ALLOWED_EVENTS = set(events_config.get("remnawave", {}).get("allowed_events", []))
TEMPLATE_PATH = Path(__file__).parent.parent / "templates"

async def handle_remnawave_webhook(request: web.Request) -> web.Response:
    """
    Основная функция-обработчик вебхуков Remnawave.

    Шаги:
    1. Чтение тела запроса как сырого текста (raw_body)
    2. Проверка подписи X-Remnawave-Signature через verify_remnawave_signature
    3. Парсинг JSON после успешной валидации
    4. Проверка, разрешено ли событие для обработки
    5. Выбор шаблона уведомления в зависимости от типа события
    6. Подготовка текста сообщения для Telegram с использованием Jinja2
    7. Отправка сообщения в Telegram
    8. Логирование обработки события
    """
    # Чтение тела запроса
    raw_body = await request.text()
    signature = request.headers.get("X-Remnawave-Signature", "")

    """
    Проверка подписи вебхука.
    Если подпись некорректна, возвращаем 403 и логируем предупреждение.
    """
    if not verify_remnawave_signature(raw_body, signature, settings.remnawave_webhook_secret):
        logger.warning("Remnawave webhook rejected: invalid signature")
        return web.Response(status=403, text="Invalid signature")

    # Попытка распарсить JSON после проверки подписи
    try:
        body = json.loads(raw_body)
    except Exception:
        body = {"raw": raw_body}

    event = body.get("event", "unknown")
    data = body.get("data", {})

    """
    Проверка разрешённых событий.
    Если событие не входит в список ALLOWED_EVENTS, игнорируем его.
    """
    if event not in ALLOWED_EVENTS:
        logger.info(f"Ignored event: {event}")
        return web.Response(text="Ignored", status=200)

    """
    Выбор шаблона уведомления в зависимости от типа события:
    - Node события -> node.html
    - Service события -> service.html
    - Infra Billing события -> billing.html
    - Прочие события -> generic.html
    """
    if event.startswith("node."):
        template_file = TEMPLATE_PATH / "node.html"
        if "activeInternalSquads" in data:
            data["activeInternalSquads"] = [s.get("name") for s in data["activeInternalSquads"]]
    elif event.startswith("service."):
        template_file = TEMPLATE_PATH / "service.html"
        login = data.get("loginAttempt", {})
        data.update(login)
    elif event.startswith("crm.infra_billing_node_payment"):
        template_file = TEMPLATE_PATH / "billing.html"
        if data.get("nextBillingAt"):
            from datetime import datetime
            dt = datetime.fromisoformat(data["nextBillingAt"])
            data["nextBillingAt"] = dt.strftime("%d.%m.%Y %H:%M UTC")
    else:
        template_file = TEMPLATE_PATH / "generic.html"
        data["raw"] = json.dumps(data, indent=2)

    """
    Рендер сообщения с использованием Jinja2.
    Подставляем данные из payload в шаблон.
    """
    with open(template_file, "r", encoding="utf-8") as f:
        template = Template(f.read())
    message_text = template.render(event=event, **data)

    """
    Отправка сообщения в Telegram.
    Если длина превышает лимит Telegram, усекаем текст.
    """
    MAX_TELEGRAM_LENGTH = 4000
    if len(message_text) > MAX_TELEGRAM_LENGTH:
        message_text = message_text[:MAX_TELEGRAM_LENGTH] + "\n...truncated..."

    await bot.send_message(
        settings.telegram_chat_id,
        message_text,
        parse_mode="HTML"
    )

    """
    Логируем успешную обработку события и возвращаем 200 OK.
    """
    logger.info(f"Remnawave webhook processed: {event}")
    return web.Response(text="OK", status=200)
