from aiohttp import web
import json
from pathlib import Path
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from datetime import datetime, timedelta
from aiogram import Bot

from ..utils.config import settings
from ..utils.logger import logger
from ..utils.verify_signature import verify_remnawave_signature

bot = Bot(token=settings.telegram_bot_token)

"""
Загрузка конфигурации разрешённых событий из YAML.
Файл events.yaml содержит список событий, которые мы хотим обрабатывать.
"""
CONFIG_PATH = Path(__file__).parent.parent / "config" / "events.yaml"
TEMPLATE_PATH = Path(__file__).parent.parent / "templates"

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    events_config = yaml.safe_load(f)

ALLOWED_EVENTS = set(events_config.get("remnawave", {}).get("allowed_events", []))

"""
Инициализация Jinja2 окружения.
Добавляем datetime и прочие глобальные функции в шаблоны.
"""
env = Environment(
    loader=FileSystemLoader(TEMPLATE_PATH),
    autoescape=select_autoescape(['html']),
    trim_blocks=True,
    lstrip_blocks=True
)
env.globals.update({
    "datetime": datetime,
    "timedelta": timedelta,  
    "len": len,
    "str": str
})



async def handle_remnawave_webhook(request: web.Request) -> web.Response:
    """
    Основная функция-обработчик вебхуков Remnawave.

    Шаги:
    1. Чтение тела запроса (raw_body)
    2. Проверка подписи (X-Remnawave-Signature)
    3. Парсинг JSON
    4. Проверка, разрешено ли событие
    5. Выбор шаблона по типу события
    6. Рендер сообщения через Jinja2
    7. Отправка в Telegram
    8. Логирование результата
    """

    # Читаем тело запроса
    raw_body = await request.text()
    signature = request.headers.get("X-Remnawave-Signature", "")

    """
    Проверяем подпись вебхука.
    Если подпись некорректна — логируем и возвращаем 403.
    """
    if not verify_remnawave_signature(raw_body, signature, settings.remnawave_webhook_secret):
        logger.warning("Remnawave webhook rejected: invalid signature")
        return web.Response(status=403, text="Invalid signature")

    # Пробуем распарсить JSON
    try:
        body = json.loads(raw_body)
    except Exception:
        body = {"raw": raw_body}

    event = body.get("event", "unknown")
    data = body.get("data", {})

    """
    Проверяем, разрешено ли событие.
    Если нет — игнорируем.
    """
    if event not in ALLOWED_EVENTS:
        logger.info(f"Ignored event: {event}")
        return web.Response(text="Ignored", status=200)

    """
    Определяем шаблон для события:
    - node.* -> node.html
    - service.* -> service.html
    - crm.infra_billing_node_payment.* -> billing.html
    - остальное -> generic.html
    """
    if event.startswith("node."):
        template_name = "node.html"

        # Приводим числовые значения к float
        for key in ("trafficUsedBytes", "trafficLimitBytes", "consumptionMultiplier"):
            if key in data and data[key] is not None:
                try:
                    data[key] = float(data[key])
                except (ValueError, TypeError):
                    data[key] = 0.0

        if "activeInternalSquads" in data:
            data["activeInternalSquads"] = [s.get("name") for s in data["activeInternalSquads"]]

    elif event.startswith("service."):
        template_name = "service.html"
        login = data.get("loginAttempt", {})
        data.update(login)

    elif event.startswith("crm.infra_billing_node_payment"):
        template_name = "billing.html"
        if data.get("nextBillingAt"):
            try:
                dt = datetime.fromisoformat(data["nextBillingAt"])
                data["nextBillingAt"] = dt.strftime("%d.%m.%Y %H:%M UTC")
            except Exception:
                pass

    else:
        template_name = "generic.html"
        data["raw"] = json.dumps(data, indent=2)

    """
    Рендерим шаблон через Jinja2.
    Подставляем event и данные из payload.
    """
    template = env.get_template(template_name)
    message_text = template.render(event=event, **data)

    """
    Отправляем сообщение в Telegram.
    Если превышен лимит 4000 символов — усекаем.
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
    Логируем успешную обработку и возвращаем 200 OK.
    """
    logger.info(f"Remnawave webhook processed: {event}")
    return web.Response(text="OK", status=200)
