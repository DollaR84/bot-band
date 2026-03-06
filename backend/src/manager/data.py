from dataclasses import dataclass


@dataclass(slots=True)
class DefaultData:
    api_id: int
    api_hash: str
    phone: str
    sdk: str = "Windows 10"
    device: str = "PC 64bit"
    app_version: str = "5.11.1"
    lang_code: str = "uk"
