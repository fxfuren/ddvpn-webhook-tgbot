import hmac
import hashlib
import json
import logging

def verify_remnawave_signature(body, signature, secret):
    """
    Validate Remnawave webhook signature (HMAC SHA256).
    Works for both dict and raw string bodies.
    """
    if isinstance(body, str):
        original_body = body
        logging.debug("Body is string, parsing for logging...")
        try:
            _ = json.loads(body)  # можно для логов, но не нужно менять original_body
        except json.JSONDecodeError as e:
            logging.warning("Failed to parse body for logging: %s", e)
            # Но original_body оставляем как есть для подписи
    else:
        # Словарь/список: сериализуем без пробелов и лишних символов
        original_body = json.dumps(body, separators=(',', ':'))

    computed_signature = hmac.new(
        secret.encode('utf-8'),
        original_body.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    valid = hmac.compare_digest(computed_signature, signature)
    if not valid:
        logging.warning("Invalid Remnawave webhook signature!")
    return valid
