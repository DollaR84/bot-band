from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Type

from config import LLMConfig


class BaseModels(ABC):
    _collections: dict[str, Type[BaseModels]] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        name = cls.get_name()
        if name not in cls._collections:
            cls._collections[name] = cls

    @classmethod
    def get_name(cls) -> str:
        _name = cls.__name__.replace("Models", "")
        return _name

    @classmethod
    def get(cls, name: str, *args: Any, **kwargs: Any) -> BaseModels:
        collection_cls = cls._collections.get(name)
        if collection_cls is None:
            raise ValueError(f"collection '{name}' does not exist")

        return collection_cls(*args, **kwargs)

    @classmethod
    def get_names(cls) -> list[str]:
        data = dict(sorted(cls._collections.items()))
        return list(data.keys())

    def __init__(self, config: LLMConfig):
        self.config = config

    @abstractmethod
    def __call__(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def params(self) -> dict[str, Any]:
        raise NotImplementedError
