import asyncio
import random

from pyrogram import Client, enums, filters
from pyrogram.types import Message

from config import Config
from context import ContextManager
from llm import LLMService


class TelegramManager:

    def __init__(self, config: Config, db: ContextManager, llm: LLMService):
        self.config = config
        self.db = db
        self.llm = llm

        self.clients: list[Client] = []

    def _setup_clients(self) -> None:
        self.clients = [
            Client(
                name=session,
                api_id=self.config.telegram.api_id,
                api_hash=self.config.telegram.api_hash,
                workdir=self.config.telegram.workdir,
            ) for session in self.config.behavior.bot_sessions
        ]

    def register_handlers(self) -> None:
        for client in self.clients:
            client.on_message(
                filters.chat(self.config.group.target_id)
            )(self.handle_group_message)

            client.on_message(
                filters.private & ~filters.me
            )(self.handle_private_message)

    async def start_all(self) -> None:
        self._setup_clients()
        self.register_handlers()

        target_id = self.config.group.target_id
        for client in self.clients:
            await client.start()
            client.me = await client.get_me()

            try:
                await client.get_chat(target_id)

                members_gen = client.get_chat_members(target_id, limit=1)
                if members_gen is not None:
                    async for _ in members_gen:
                        break
                else:
                    name = client.me.first_name
                    print(f"⚠️[{name}] Не вдалося отримати генератор учасників")

                print("Чат успішно знайдено та додано до кешу сесії")
            except Exception as error:
                print(f"Не вдалося знайти чат: {error}")

            await asyncio.sleep(2)
        print(f"Запущено ботів: {len(self.clients)}")

    async def stop_all(self) -> None:
        tasks = [client.stop() for client in self.clients if client.is_connected]
        await asyncio.gather(*tasks)

    async def simulate_typing(self, client: Client, chat_id: int) -> None:
        await client.send_chat_action(chat_id, enums.ChatAction.TYPING)

        delay = random.uniform(self.config.behavior.min_delay, self.config.behavior.max_delay)
        await asyncio.sleep(delay)

    async def handle_private_message(self, client: Client, message: Message) -> None:
        new_topic = None
        if client.me and client.me.id == self.config.group.admin_id:
            new_topic = message.text
        if not new_topic:
            return

        await self.db.set_topic(new_topic)

        trigger_text = f"Нова тема для обговорення: {new_topic}"
        await client.send_message(self.config.group.target_id, trigger_text)

        await self.db.add_message("assistant", (await client.get_me()).first_name, trigger_text)

    async def handle_group_message(self, client: Client, message: Message) -> None:
        sender_name = message.from_user.first_name if message.from_user else "Unknown"
        if client == self.clients[0]:
            await self.db.add_message("user", sender_name, message.text)

        target_client = None
        is_reply = False
        if message.reply_to_message and (user := message.reply_to_message.from_user):
            if client.me and client.me.id == user.id:
                target_client = client
                is_reply = True
            else:
                return

        else:
            last_id = await self.db.get_last_poster()
            if client.me and client.me.id == last_id:
                return

            if random.random() < 0.5:
                target_client = client

        if target_client:
            asyncio.create_task(self.process_response(target_client, message, is_reply))

    async def process_response(self, client: Client, message: Message, is_reply: bool = False) -> None:
        await asyncio.sleep(random.uniform(1, 3))

        context = await self.db.get_context()
        topic = await self.db.get_topic()
        bot_name = client.me.first_name if client.me else (await client.get_me()).first_name

        response_text = await self.llm.generate_reply(context, topic, bot_name)
        await self.simulate_typing(client, message.chat.id)

        typing_delay = min(len(response_text) * 0.1, 10)
        await asyncio.sleep(typing_delay)

        if is_reply:
            await message.reply_text(response_text)
        else:
            await client.send_message(message.chat.id, response_text)

        await self.db.set_last_poster(client.me.id if client.me else (await client.get_me()).id)
        await self.db.add_message("assistant", bot_name, response_text)
