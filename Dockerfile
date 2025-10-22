FROM python:3.12-slim

WORKDIR /app

# Копируем только requirements
COPY bot/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Копируем весь проект в контейнер
COPY bot /app/bot

# Запускаем как пакет
CMD ["python", "-m", "bot.main"]
