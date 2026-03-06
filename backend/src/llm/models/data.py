from dataclasses import dataclass
from datetime import datetime
from typing import Self


@dataclass(slots=True)
class GrokModel:
    id: str
    created: datetime
    object: str
    owned_by: str

    @classmethod
    def from_dict(cls, data: dict[str, str | int]) -> Self:
        return cls(
            id=str(data["id"]),
            created=datetime.fromtimestamp(int(data["created"])),
            object=str(data["object"]),
            owned_by=str(data["owned_by"]),
        )
