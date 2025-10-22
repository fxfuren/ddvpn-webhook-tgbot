import logging
from logging.handlers import RotatingFileHandler
import sys

logger = logging.getLogger("ddvpn-webhook")
logger.setLevel(logging.INFO)

if not logger.handlers:
    # Консоль
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    # Файл
    fh = RotatingFileHandler("bot.log", maxBytes=5 * 1024 * 1024, backupCount=3)
    fh.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)

def setup_logger():
    return logger
