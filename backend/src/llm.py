import random
from typing import Any, cast

from openai import AsyncOpenAI

from config import Config


class LLMService:

    def __init__(self, config: Config):
        self.client = AsyncOpenAI(
            base_url=config.llm.base_url,
            api_key=config.llm.api_key,
        )
        self.model = config.llm.model

    async def generate_reply(self, context: list[dict[str, str]], topic: str, bot_name: str) -> str:
        system_instruction = (
            f"Ти — {bot_name}, учасник живого чату в Telegram. "
            f"Зараз ми обговорюємо тему: '{topic}'.\n\n"
            "ПРАВИЛА СПІЛКУВАННЯ:\n"
            "1. Пиши як людина: коротко, використовуй сленг, маленькі літери, іноді емодзі, але не перебільшуй.\n"
            "2. Можеш припускатися однієї друкарської помилки в довгих словах для реалістичності.\n"
            "3. Не будь занадто ввічливим ШІ-помічником. Ти — просто учасник дискусії.\n"
            "4. Якщо до тебе звернулися особисто (реплай), відповідай конкретно на питання.\n"
            "5. Не використовуй фрази типу 'Як я можу вам допомогти?' або 'Я — модель ШІ'.\n"
            "6. Твоя відповідь має бути від 1 до 3 коротких речень."
            "7. ВІДПОВІДАЙ ТІЛЬКИ ТЕКСТОМ ПОВІДОМЛЕННЯ. Не пиши своє ім'я або 'Ім'я: ' на початку."
        )

        messages: list[dict[str, str]] = [{"role": "system", "content": system_instruction}]

        for msg in context:
            role = "assistant" if msg.get("name") == bot_name else "user"
            content = f"{msg.get('name', 'Unknown')}: {msg.get('content', '')}"
            messages.append({"role": role, "content": content})

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=cast(Any, messages),
                temperature=0.85,
                presence_penalty=0.6,
                frequency_penalty=0.5,
                max_tokens=200,
            )

            reply = response.choices[0].message.content
            reply = reply.strip() if reply else ""
            if reply.startswith(f"{bot_name}:"):
                reply = reply.replace(f"{bot_name}:", "")
            reply = reply.lstrip(",.:; ")

            return reply
        except Exception as error:
            print(f"[!] Помилка LLM: {error}")
            return random.choice(["Лоол", "Ахах, згоден", "Мда...", "Ну таке"])
