from pydantic_settings import BaseSettings, SettingsConfigDict


class TelegramConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="TELEGRAM_")

    api_id: int
    api_hash: str
    workdir: str

    target_username: str
