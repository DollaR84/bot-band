import asyncio
import json
from pathlib import Path
import random
import sqlite3
import time
from typing import Optional

from opentele.td import TDesktop
from opentele.tl import TelegramClient
from opentele.api import API, UseCurrentSession
from telethon.errors import FloodWaitError
from telethon.tl.types import Channel, Chat

from config import TelegramConfig


class SessionManager:

    def __init__(self, config: TelegramConfig, workdir: Path):
        self.config = config
        self.workdir = workdir

    async def _get_telethon_params(self, telethon_client: TelegramClient) -> tuple[int, bytes, int, int, int, str]:
        if not telethon_client.is_connected():
            await telethon_client.connect()

        me = await telethon_client.get_me()
        auth_key = bytes(telethon_client.session.auth_key.key)
        dc_id = telethon_client.session.dc_id

        entity = await telethon_client.get_entity(self.config.target_username)
        group_id = entity.id
        access_hash = getattr(entity, "access_hash", 0)
        p_type = type(entity).__name__.lower()

        if isinstance(entity, Channel):
            group_id = int(f"-100{group_id}") if not str(group_id).startswith("-100") else group_id
        elif isinstance(entity, Chat):
            group_id = -group_id if not str(group_id).startswith("-") else group_id

        await telethon_client.disconnect()
        return dc_id, auth_key, me.id, group_id, access_hash, p_type

    async def telethon2pyrogram(self, telethon_client: TelegramClient, name: str, api_id: int, api_hash: str) -> None:
        dc_id, auth_key, user_id, group_id, access_hash, p_type = await self._get_telethon_params(telethon_client)
        await self._save_pyro_sql(name, dc_id, auth_key, user_id, api_id, api_hash, group_id, access_hash, p_type)

    async def _save_pyro_sql(
            self,
            name: str,
            dc_id: int,
            auth_key: bytes,
            user_id: int,
            api_id: int,
            api_hash: str,
            group_id: int,
            access_hash: int,
            p_type: str,
    ) -> None:
        db_path = (self.workdir / f"{name}.session").resolve()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                dc_id     INTEGER,
                api_id    INTEGER,
                test_mode INTEGER,
                auth_key BLOB,
                date INTEGER,
                user_id INTEGER,
                is_bot INTEGER,
                api_hash TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS peers (
                id INTEGER PRIMARY KEY,
                access_hash INTEGER,
                type TEXT,
                username TEXT,
                phone_number TEXT,
                last_update_on INTEGER DEFAULT 0
            )
        """)
        cursor.execute("CREATE TABLE IF NOT EXISTS version (number INTEGER)")

        cursor.execute("CREATE INDEX idx_peers_id ON peers (id)")
        cursor.execute("CREATE INDEX idx_peers_username ON peers (username)")

        cursor.execute(
            """INSERT INTO sessions (dc_id, api_id, test_mode, auth_key, date, user_id, is_bot, api_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (dc_id, api_id, 0, auth_key, int(time.time()), user_id, 0, api_hash)
        )
        cursor.execute(
            "INSERT OR REPLACE INTO peers (id, access_hash, type, username, last_update_on) VALUES(?, ?, ?, ?, ?)",
            (group_id, access_hash, p_type, self.config.target_username, int(time.time()))
        )
        cursor.execute("INSERT INTO version (number) VALUES (?)", (3,))

        conn.commit()
        conn.close()


class Converter:

    def __init__(self) -> None:
        self.config = TelegramConfig()
        self.workdir = Path(self.config.workdir)

    async def run(self) -> None:
        subfolders = [
            folder for folder in self.workdir.iterdir()
            if folder.is_dir() and folder.name != "__MACOSX"
        ]

        for folder in subfolders:
            folder_parts = folder.name.split('-')
            if len(folder_parts) > 1:
                phone_number = folder_parts[-1]
            else:
                phone_number = folder.name

            target_session_file = self.workdir / f"{phone_number}.session"
            if target_session_file.exists():
                print(f"⏩ Skip: {phone_number}.session already exists in root {self.workdir}.")
                continue
            print(f"🚀 processing: {folder.name} (phone: {phone_number})")

            session_file = next(folder.glob("*.session"), None)
            json_file = next(folder.glob("*.json"), None)
            tdata_dir = folder / "tdata"

            await self.convert(folder, phone_number, session_file, json_file, tdata_dir)
            delay = random.uniform(5, 20)
            await asyncio.sleep(delay)

    async def convert(
            self,
            folder: Path,
            phone_number: str,
            session_file: Optional[Path] = None,
            json_file: Optional[Path] = None,
            tdata: Optional[Path] = None,
    ) -> None:
        session = SessionManager(self.config, self.workdir)

        try:
            if session_file and json_file:
                data = json.loads(json_file.read_text())
                api_id = data.get("app_id")
                api_hash = data.get("app_hash")
                two_fa_password = data.get("twoFA")

                myapp = API.TelegramDesktop(api_id=api_id, api_hash=api_hash)
                client = TelegramClient(str(session_file), api=myapp)
                if await self.check_flood(client, two_fa_password):
                    await session.telethon2pyrogram(client, phone_number, api_id, api_hash)
                    print(f"✅ converted to pyrogram {phone_number}.session")

            elif tdata and tdata.exists():
                password_file = tdata / "Password2FA.txt"
                two_fa_password = password_file.read_text().strip() if password_file.exists() else None

                td = TDesktop(str(tdata))
                client = await td.ToTelethon(flag=UseCurrentSession, password=two_fa_password)
                if await self.check_flood(client, two_fa_password):
                    await session.telethon2pyrogram(
                        client,
                        phone_number,
                        API.TelegramDesktop.api_id,
                        API.TelegramDesktop.api_hash
                    )
                    print(f"✅ converted from TData to pyrogram {phone_number}.session")

            else:
                print(f"⚠️ no files found in {folder.name}")

        except Exception as error:
            print(f"❌ ERROR: {error}")

    async def check_flood(self, client: TelegramClient, password: Optional[str] = None) -> bool:
        print("🔗 Attempting to connect to a session...")
        result = False
        try:
            await client.connect()

            if not await client.is_user_authorized():
                if password:
                    try:
                        await client.sign_in(password=password)
                    except Exception as error:
                        print(f"❌ Failed to login with password: {error}")
                        return result
                else:
                    print("❌ Session is invalid and 2FA password not provided.")
                    return result

            me = await client.get_me()
            print(f"✅ Account {me.first_name} is clean! No block.")

            result = True
        except FloodWaitError as error:
            total_seconds = error.seconds
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            print("⏳ WARNING: Detected FloodWait!")
            print(f"All that's left to do is wait: {hours} hours {minutes} minutes ({total_seconds} seconds)")

        except Exception as error:
            print(f"❓ Another error occurred: {error}")
        finally:
            await client.disconnect()

        return result


if __name__ == "__main__":
    converter = Converter()
    asyncio.run(converter.run())
