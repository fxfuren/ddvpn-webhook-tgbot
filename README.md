# ddvpn-webhook-tgbot

Webhook-бот для интеграции **Remnawave** и **Observer** с Telegram.
Бот принимает вебхуки о событиях нод, сервисов, платежей и нарушениях пользователей, формирует красиво оформленные уведомления и отправляет их в указанный Telegram-чат.

---

## Функционал

### 1. Remnawave

Бот принимает вебхуки от Remnawave и фильтрует их по списку разрешённых событий, который хранится в `config/events.yaml`.

События могут относиться к разным категориям: ноды, сервисы, платежи и т.д.

Все уведомления формируются через **Jinja2 шаблоны** (`templates/`) и отправляются в Telegram с красивым оформлением, включая динамический хештег события (`#event_name`).

```
> ⚠️ Список разрешённых событий можно увеличивать или изменять в любой момент, редактируя `config/events.yaml`. Новые события будут автоматически обрабатываться ботом без изменения кода.
> ⚠️ Шаблон сообщений можно менять в папке `templates` без изменения кода бота.
```

---

### 2. Observer

Бот принимает вебхуки об нарушениях пользователей, например при превышении лимита IP-адресов:

**Пример JSON:**

```json
{
	"user_identifier": "54_217217281",
	"detected_ips_count": 13,
	"limit": 12,
	"all_user_ips": ["1.1.1.1", "2.2.2.2", "3.3.3.3"],
	"block_duration": "5m",
	"violation_type": "ip_limit_exceeded"
}
```

**Пример уведомления в Telegram:**

```
🚨 #alert
➖➖➖➖➖➖➖➖➖
👤 Пользователь: 54_217217281
📡 Превышен лимит IP-адресов: 13 / 12
⏱ Заблокировано на: 5m
🖧 IP-адреса:
1.1.1.1, 2.2.2.2, 3.3.3.3
⚠ Тип нарушения: ip_limit_exceeded
```

Для безопасности можно указывать секретный токен в URL (`/webhook/alert/<ALERT_SECRET>`), чтобы никто посторонний не мог слать фейковые уведомления.

> ⚠️ Изменять шаблоны сообщений можно в папке `templates` - бот будет использовать их автоматически.

---

## Установка

### 1. Клонирование репозитория

```bash
git clone https://github.com/fxfuren/ddvpn-webhook-tgbot.git
cd ddvpn-webhook-tgbot/bot
```

### 2. Создание виртуального окружения и установка зависимостей

```bash
python -m venv venv
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate      # Windows

pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Настройка `.env`

Создайте файл `.env` в корне `bot`:

```env
TELEGRAM_BOT_TOKEN=ваш_токен
TELEGRAM_CHAT_ID=ваш_чат_id
BOT_INTERNAL_PORT=8080
DOMAIN=https://ваш_домен.com

# Remnawave
REMNAWAVE_WEBHOOK_SECRET=секрет_для_проверки_подписей

# Alert webhook (Observer)
ALERT_WEBHOOK_SECRET=секрет_для_alerts
```

---

## Запуск

### Локальная разработка (ngrok)

1. Установите [ngrok](https://ngrok.com/) и создайте туннель:

```bash
ngrok http 8080
```

2. В `.env` укажите `DOMAIN=https://<ngrok-ссылка>`

3. Настройте Remnawave и Observer на ваш ngrok URL:

```
REMNAWAVE_WEBHOOK_URL=https://<ngrok-ссылка>/webhook/remnawave
ALERT_WEBHOOK_URL=https://<ngrok-ссылка>/webhook/alert/<ALERT_SECRET>
```

4. Запустите бота:

```bash
python -m bot.main
```

### Развёртывание на VPS с доменом через Docker Compose

1. Настройте домен и вебхуки:

```
REMNAWAVE_WEBHOOK_URL=https://ваш_домен.com/webhook/remnawave
ALERT_WEBHOOK_URL=https://ваш_домен.com/webhook/alert/<ALERT_SECRET>
```

2. Соберите и запустите:

```bash
docker-compose up -d
```

---

## Структура проекта

```
bot/
├── main.py                 # Точка входа, запускает aiohttp сервер
├── handlers/
│   ├── remnawave_handler.py  # Обработка webhook Remnawave
│   ├── alert_handler.py      # Обработка AlertPayload от Observer
├── utils/
│   ├── config.py           # Настройка и загрузка .env
│   ├── logger.py           # Настройка логирования
│   └── verify_signature.py # Проверка HMAC подписи Remnawave
├── templates/
│   ├── node.html
│   ├── service.html
│   ├── billing.html
│   ├── generic.html
│   └── alert.html          # Шаблон для уведомлений Observer
├── config/
│   └── events.yaml         # Список разрешённых событий (редактируется)
└── requirements.txt
docker-compose.yml
Dockerfile
nginx.conf
.env.example


```

---

## Особенности

- Красивое оформление сообщений с HTML и эмодзи.
- Динамические хештеги для типа события (`#login_attempt_success`, `#ip_limit_exceeded`).
- Валидация подписей Remnawave через HMAC SHA256.
- Защита вебхуков AlertPayload через секрет в URL.
- Логи в консоль и в файл `bot.log` с ротацией.
- Изменяемые шаблоны сообщений через `templates/` без изменения кода.
- Поддержка Docker Compose для быстрого развёртывания на VPS.
