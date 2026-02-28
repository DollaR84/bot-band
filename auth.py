import asyncio
from pathlib import Path

from pyrogram import Client
from pydantic_settings import BaseSettings, SettingsConfigDict


class TelegramConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env_auth", env_prefix="TELEGRAM_")

    api_id: int
    api_hash: str
    workdir: str = "./sessions/"


async def create_session() -> None:
    config = TelegramConfig()
    session_name = input("Enter session name (example, account): ")

    workdir = Path(config.workdir)
    workdir.mkdir(parents=True, exist_ok=True)

    async with Client(session_name, api_id=config.api_id, api_hash=config.api_hash, workdir=str(workdir)) as app:
        me = await app.get_me()
        print("✅ session created successfully!")
        print(f"Bot/Account: {me.first_name} (@{me.username})")
        print(f"File {session_name}.session ready.")


if __name__ == "__main__":
    asyncio.run(create_session())
