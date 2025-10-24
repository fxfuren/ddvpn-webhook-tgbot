# ddvpn-webhook-tgbot

Webhook-бот для интеграции **[Remnawave](https://github.com/remnawave/panel)** и **[Observer](https://github.com/0FL01/remnawave-observer)** с Telegram.
Бот принимает вебхуки о событиях нод, сервисов, платежей и нарушениях пользователей, формирует красиво оформленные уведомления и отправляет их в указанный Telegram-чат.

## Функционал

### 1. Remnawave

Бот принимает вебхуки от Remnawave и фильтрует их по списку разрешённых событий, который хранится в `config/events.yaml`.

События могут относиться к разным категориям: ноды, сервисы, платежи и т.д.

Все уведомления формируются через **Jinja2 шаблоны** (`templates/`) и отправляются в Telegram с красивым оформлением, включая динамический хештег события (`#event_name`).

> ⚠️ Список разрешённых событий можно увеличивать или изменять в любой момент, редактируя `config/events.yaml`. Новые события будут автоматически обрабатываться ботом без изменения кода.

> ⚠️ Шаблон сообщений можно менять в папке `templates` без изменения кода бота.

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

## Развёртывание на VPS с доменом через Docker Compose

### 1. Подготовка сертификатов

Перед запуском убедитесь, что у вас есть SSL-сертификаты для вашего домена (например, через Let’s Encrypt) и они находятся на VPS по пути:

```
/etc/letsencrypt/live/<ваш_домен>/fullchain.pem
/etc/letsencrypt/live/<ваш_домен>/privkey.pem
```

> ⚠️ Сертификаты должны быть созданы заранее.

### 2. Подключение сертификатов к `remnawave-nginx`

Если контейнер `remnawave-nginx` уже существует, добавьте монтирование сертификатов в ваш существующий `docker-compose.yml`:

```yaml
volumes:
  - /etc/letsencrypt/live/<ваш_домен>/fullchain.pem:/etc/nginx/ssl/<ваш_домен>/fullchain.pem:ro
  - /etc/letsencrypt/live/<ваш_домен>/privkey.pem:/etc/nginx/ssl/<ваш_домен>/privkey.pem:ro
```

### 3. Конфигурация Nginx для сервиса `remnawave-nginx`

Добавьте блок для вашего сервиса в `nginx.conf`:

```nginx
server {
    server_name <ваш_домен>;

    listen unix:/dev/shm/nginx.sock ssl proxy_protocol;
    http2 on;

    ssl_certificate "/etc/nginx/ssl/<ваш_домен>/fullchain.pem";
    ssl_certificate_key "/etc/nginx/ssl/<ваш_домен>/privkey.pem";
    ssl_trusted_certificate "/etc/nginx/ssl/<ваш_домен>/fullchain.pem";

    location / {
        proxy_pass http://127.0.0.1:8080; # Порт, на котором работает ваш сервис
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 4. Настройка переменных окружения

Установите вебхуки для **remnawave** и **observer-alert**:

```bash
REMNAWAVE_WEBHOOK_URL=https://<ваш_домен>/webhook/remnawave
ALERT_WEBHOOK_URL=https://<ваш_домен>/webhook/alert/<ALERT_SECRET>
```

### 5. Применение изменений

Перезапустите `remnawave-nginx`, чтобы применить новые сертификаты и конфигурацию:

```bash
docker-compose restart remnawave-nginx
```

Теперь ваш сервис будет работать через SSL на вашем домене через существующий контейнер `remnawave-nginx`.

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
.env.example
```

## Особенности

- Красивое оформление сообщений с HTML и эмодзи.
- Динамические хештеги для типа события (`#login_attempt_success`, `#ip_limit_exceeded`).
- Валидация подписей Remnawave через HMAC SHA256.
- Защита вебхуков AlertPayload через секрет в URL.
- Логи в консоль и в файл `bot.log` с ротацией.
- Изменяемые шаблоны сообщений через `templates/` без изменения кода.
- Поддержка Docker Compose для быстрого развёртывания на VPS.
