import asyncio
from pathlib import Path
import random

from pyrogram import Client, enums, filters
from pyrogram.types import Message

from config import Config
from context import ContextManager
from llm import LLMService

from .settings import TelethonSettings


class TelegramManager:

    def __init__(self, config: Config, db: ContextManager, llm: LLMService):
        self.config = config
        self.db = db
        self.llm = llm

        self.clients: list[Client] = []

    def register_handlers(self) -> None:
        for client in self.clients:
            client.on_message(
                filters.chat(self.config.group.target_id)
            )(self.handle_group_message)

            client.on_message(
                filters.private & ~filters.me
            )(self.handle_private_message)

    def _setup_clients(self) -> None:
        telethon = TelethonSettings(self.config.telegram)
        sessions_path = Path(self.config.telegram.workdir)

        for session_file in sessions_path.glob("*.session"):
            data = telethon(session_file.stem)
            if not data:
                continue

            client = Client(
                name=session_file.stem,
                api_id=data.api_id,
                api_hash=data.api_hash,
                workdir=self.config.telegram.workdir,
            )
            if client:
                self.clients.append(client)

    async def join_if_needed(self, client: Client, chat_id: int) -> None:
        try:
            await client.get_chat_member(chat_id, "me")

        except Exception:
            try:
                print(f"📡 [{client.name}] Спроба вступу в чат {chat_id}...")
                await client.join_chat(chat_id)
                print(f"✅ [{client.name}] Успішно вступив до чату")
            except Exception as error:
                print(f"[{client.name}] Сталася помилка: {error}")

    async def start_all(self) -> None:
        self._setup_clients()
        self.register_handlers()

        for client in self.clients:
            try:
                await client.start()
                if not client.is_connected:
                    print(f"❌ [{client.name}] Клієнт не підключений!")
                    continue

                await asyncio.sleep(1)
                me = await client.get_me()
                print(f"🚀 бот {me.first_name} {me.last_name or ''} готовий до роботи!")

                chat = await client.get_chat(self.config.group.target_id)
                print(f"✅ [{client.name}] чат {chat.title} знайдено в кеші.")
                await self.join_if_needed(client, self.config.group.target_id)

            except Exception as error:
                print(f"❌ [{client.name}] Помилка при запуску: {error}")

            delay = random.uniform(self.config.behavior.min_delay, self.config.behavior.max_delay)
            await asyncio.sleep(delay)
        print(f"Запущено ботів: {len(self.clients)}")

    async def stop_all(self) -> None:
        tasks = [client.stop() for client in self.clients if client.is_connected]
        await asyncio.gather(*tasks)

    async def simulate_typing(self, client: Client, chat_id: int, text_lenght: int) -> None:
        await client.send_chat_action(chat_id, enums.ChatAction.TYPING)

        typing_delay = min(text_lenght * 0.1, 10)
        await asyncio.sleep(typing_delay)

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

            if random.random() < 0.3:
                target_client = client

        if target_client:
            asyncio.create_task(self.process_response(target_client, message, is_reply))

    async def process_response(self, client: Client, message: Message, is_reply: bool = False) -> None:
        delay = random.uniform(self.config.behavior.min_delay, self.config.behavior.max_delay)
        await asyncio.sleep(delay)

        context = await self.db.get_context()
        topic = await self.db.get_topic()
        bot_name = client.me.first_name if client.me else (await client.get_me()).first_name

        response_text = await self.llm.generate_reply(context, topic, bot_name)
        await self.simulate_typing(client, message.chat.id, len(response_text))

        if is_reply:
            await message.reply_text(response_text)
        else:
            await client.send_message(message.chat.id, response_text)

        await self.db.set_last_poster(client.me.id if client.me else (await client.get_me()).id)
        await self.db.add_message("assistant", bot_name, response_text)
