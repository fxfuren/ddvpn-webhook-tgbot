import logging
from logging.handlers import RotatingFileHandler
import sys

"""
Модуль logger.py настраивает логирование для проекта ddvpn-webhook-tg.

Используется:
- RotatingFileHandler для логов в файл с ротацией (ограничение размера и количества файлов)
- StreamHandler для вывода логов в консоль
- Единый формат логирования с временной меткой, уровнем и сообщением
"""

# Создаем объект логгера для всего проекта
logger = logging.getLogger("ddvpn-webhook")
logger.setLevel(logging.INFO)  # Уровень логирования INFO и выше

# Проверка, что хэндлеры еще не добавлены
if not logger.handlers:
    # --- Консольный хэндлер ---
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)  # Логи уровня INFO+ выводятся в консоль

    # --- Файловый хэндлер с ротацией ---
    # Файл bot.log, максимум 5 МБ на файл, хранить до 3 старых файлов
    fh = RotatingFileHandler("bot.log", maxBytes=5 * 1024 * 1024, backupCount=3)
    fh.setLevel(logging.INFO)

    # Форматирование логов: Время - Уровень - Сообщение
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)

    # Добавляем хэндлеры к логгеру
    logger.addHandler(ch)
    logger.addHandler(fh)

def setup_logger():
    """
    Возвращает настроенный объект логгера для использования в других модулях.
    
    Пример использования:
        from utils.logger import setup_logger
        logger = setup_logger()
    """
    return logger
