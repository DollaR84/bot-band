from typing import Any

import requests

from config import LLMConfig

from .base import BaseModels
from .data import GrokModel


class GrokModels(BaseModels):

    def __init__(self, config: LLMConfig):
        super().__init__(config)

        self._models: list[GrokModel] = []
        self.load()

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }

    def _get_models(self) -> list[dict[str, str | int]]:
        url = "/".join([self.config.base_url, "models"])
        try:
            response = requests.get(
                url,
                headers=self.headers,
                timeout=(3.5, 10)
            )

            response.raise_for_status()
            result: list[dict[str, str | int]] = response.json().get("data", [])
            return result

        except requests.exceptions.Timeout:
            print("Grok AI API took too long to respond when requesting models")
            return []

    def load(self) -> None:
        data = self._get_models()

        for model_data in data:
            self._models.append(
                GrokModel.from_dict(model_data)
            )

    def __call__(self) -> str:
        if not self._models:
            raise ValueError("no Grok AI models available")

        if self.config.model:
            for model in self._models:
                if model.id == self.config.model:
                    return model.id
        return self._models[0].id

    @property
    def params(self) -> dict[str, Any]:
        return {
            "temperature": 0.85,
            "max_tokens": 200,
        }
