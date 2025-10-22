import hmac
import hashlib
import json
import logging

"""
Модуль verify_signature.py отвечает за проверку подписи вебхуков Remnawave.

Используется алгоритм HMAC SHA256 для проверки целостности данных.
Поддерживаются два типа тела запроса:
- dict/list — сериализуется в JSON без пробелов для HMAC
- str — используется как есть
"""

def verify_remnawave_signature(body, signature, secret):
    """
    Проверяет подпись вебхука Remnawave.

    Аргументы:
        body (dict | list | str): Тело запроса вебхука
        signature (str): Подпись из заголовка X-Remnawave-Signature
        secret (str): Секретный ключ WEBHOOK_SECRET_HEADER из .env

    Возвращает:
        bool: True если подпись корректна, False если нет.

    Логирование:
        - предупреждение, если не удалось распарсить тело
        - предупреждение, если подпись некорректна
    """

    if isinstance(body, str):
        # Тело в виде строки, используем как есть для проверки HMAC
        original_body = body
        logging.debug("Body is string, attempting JSON parse for logging...")
        try:
            _ = json.loads(body)  # Для логов, не меняем original_body
        except json.JSONDecodeError as e:
            logging.warning("Failed to parse body for logging: %s", e)
    else:
        # Тело в виде dict/list, сериализуем в compact JSON
        original_body = json.dumps(body, separators=(',', ':'))

    # Вычисляем HMAC SHA256
    computed_signature = hmac.new(
        secret.encode('utf-8'),
        original_body.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    # Сравниваем подписи безопасно
    valid = hmac.compare_digest(computed_signature, signature)
    if not valid:
        logging.warning("Invalid Remnawave webhook signature!")

    return valid
