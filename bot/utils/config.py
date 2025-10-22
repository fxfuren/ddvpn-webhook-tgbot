from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    telegram_bot_token: str
    telegram_chat_id: int
    domain: str
    bot_internal_port: int = 8080
    remnawave_webhook_secret: str = ""
    remnawave_webhook_enabled: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
