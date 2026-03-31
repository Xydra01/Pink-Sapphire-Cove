from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from backend.app.core import get_settings
from backend.app.models import Dragon, UserSession


class DatabaseConfigError(RuntimeError):
    pass


async def init_db() -> None:
    settings = get_settings()
    if not settings.mongodb_uri:
        raise DatabaseConfigError("Missing MONGODB_URI environment variable.")

    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client.get_default_database() if not settings.mongodb_db else client[settings.mongodb_db]

    await init_beanie(database=db, document_models=[Dragon, UserSession])

