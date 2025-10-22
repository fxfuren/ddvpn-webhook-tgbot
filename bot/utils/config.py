from pydantic_settings import BaseSettings

"""
Класс Settings описывает конфигурацию бота и вебхуков.
Использует Pydantic BaseSettings для автоматической загрузки настроек из .env.
"""

class Settings(BaseSettings):
    """
    Основные параметры бота и вебхуков:

    telegram_bot_token : str
        Токен Telegram-бота для отправки уведомлений.

    telegram_chat_id : int
        ID чата, куда бот отправляет уведомления.

    domain : str
        Домен, на котором доступен бот/вебхуки.

    bot_internal_port : int
        Порт, на котором бот слушает входящие запросы. По умолчанию 8080.

    remnawave_webhook_secret : str
        Секрет для проверки подписи вебхуков Remnawave.

    alert_webhook_secret : str
        Секрет для проверки URL вебхуков Observer.
    """
    telegram_bot_token: str
    telegram_chat_id: int
    domain: str
    bot_internal_port: int = 8080
    remnawave_webhook_secret: str = ""
    alert_webhook_secret: str = ""

    class Config:
        """
        Конфигурация BaseSettings:
        - env_file: путь к файлу с переменными окружения
        - env_file_encoding: кодировка файла
        """
        env_file = ".env"
        env_file_encoding = "utf-8"

# Глобальный объект settings для доступа к конфигурации по всему проекту
settings = Settings()
