import json
from typing import Awaitable, cast, Optional

import redis.asyncio as aioredis

from config import Config


class ContextManager:

    def __init__(self, config: Config):
        self.config = config
        self.redis = aioredis.Redis(host=self.config.redis.host, port=self.config.redis.port, decode_responses=True)
        self.context_key = f"chat_context:{config.group.target_id}"
        self.current_topic_key = f"current_topic:{config.group.target_id}"

    async def add_message(self, role: str, name: str, text: str) -> None:
        payload = json.dumps({"role": role, "name": name, "content": text})
        await cast(Awaitable[int], self.redis.lpush(self.context_key, payload))
        await cast(Awaitable[str], self.redis.ltrim(self.context_key, 0, 20))

    async def get_context(self) -> list[dict[str, str]]:
        messages = await cast(Awaitable[list[str]], self.redis.lrange(self.context_key, 0, -1))
        return [json.loads(msg) for msg in reversed(messages)]

    async def set_topic(self, topic: str) -> None:
        await self.redis.set(self.current_topic_key, topic)

    async def get_topic(self) -> str:
        return await self.redis.get(self.current_topic_key) or "Повсякденне спілкування"

    async def set_last_poster(self, user_id: int) -> None:
        await self.redis.set(f"last_poster:{self.config.group.target_id}", user_id)

    async def get_last_poster(self) -> Optional[int]:
        value = await self.redis.get(f"last_poster:{self.config.group.target_id}")
        return int(value) if value else None

    async def clear_context(self) -> None:
        await self.redis.delete(self.context_key)
