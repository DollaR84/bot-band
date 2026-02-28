import asyncio

from config import Config
from context import ContextManager
from llm import LLMService
from manager import TelegramManager


async def main() -> None:
    config = Config()
    db = ContextManager(config)
    llm = LLMService(config)

    manager = TelegramManager(config, db, llm)

    try:
        await manager.start_all()

        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n[!] Зупинка системи...")
    finally:
        await manager.stop_all()


if __name__ == "__main__":
    asyncio.run(main())
