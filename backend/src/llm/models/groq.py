from typing import Any

from .base import BaseModels


class GroqModels(BaseModels):

    def __call__(self) -> str:
        if not self.config.model:
            raise ValueError("no set Groq AI model in .env")

        return self.config.model

    @property
    def params(self) -> dict[str, Any]:
        return {
            "temperature": 0.85,
            "presence_penalty": 0.6,
            "frequency_penalty": 0.5,
            "max_tokens": 200,
        }
