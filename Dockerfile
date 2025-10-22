FROM python:3.12-slim

WORKDIR /app
COPY bot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot /app
CMD ["python", "main.py"]