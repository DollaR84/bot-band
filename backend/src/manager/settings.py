import json
from pathlib import Path
from typing import Optional

from config import TelegramConfig

from .data import DefaultData


class TelethonSettings:

    def __init__(self, config: TelegramConfig):
        self.config = config
        self.workdir = Path(self.config.workdir)

    def __call__(self, phone_number: str) -> Optional[DefaultData]:
        subfolders = [
            subfolder for subfolder in self.workdir.iterdir()
            if subfolder.is_dir() and not subfolder.name.startswith(".") and subfolder.name != "__MACOSX"
        ]

        for folder in subfolders:
            if phone_number in folder.name:
                break
        else:
            return None

        json_file = next(folder.glob("*.json"), None)
        if not json_file:
            return None

        json_data = json.loads(json_file.read_text(encoding="utf-8"))
        data = DefaultData(
            api_id=json_data.get("app_id", self.config.api_id),
            api_hash=json_data.get("app_hash", self.config.api_hash),
            phone=json_data.get("phone", phone_number),
        )
        data.sdk = json_data.get("sdk", data.sdk)
        data.device = json_data.get("device", data.device)
        data.app_version = json_data.get("app_version", data.app_version)
        data.lang_code = json_data.get("lang_pack", data.lang_code)

        return data
