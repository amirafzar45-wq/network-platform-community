from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str
    jwt_secret: str
    api_cors_origins: str = "http://localhost"
    poll_interval_seconds: int = 30
    backup_dir: str = "/backups"
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
