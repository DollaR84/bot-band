from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class RedisConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="REDIS_")

    host: str
    port: int = 6379

    url: Optional[str] = None

    @field_validator("port")
    @classmethod
    def validate_port(cls, value: int) -> int:
        if not 0 < value < 65535:
            raise ValueError("invalid redis port")
        return value


class TelegramConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TELEGRAM_")

    api_id: int
    api_hash: str

    workdir: str = "/app/sessions/"


class GroupConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GROUP_")

    target_id: int
    admin_id: int


class LLMConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LLM_")

    base_url: str
    api_key: str
    model: str


class BehaviorConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BEHAVIOR_")

    min_delay: int = 5
    max_delay: int = 20

    bot_sessions: list[str] = Field(default_factory=list)


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_nested_delimiter="__")

    redis: RedisConfig = Field(default_factory=RedisConfig)
    telegram: TelegramConfig = Field(default_factory=TelegramConfig)
    group: GroupConfig = Field(default_factory=GroupConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    behavior: BehaviorConfig = Field(default_factory=BehaviorConfig)
