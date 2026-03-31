from __future__ import annotations

import os
from typing import AsyncIterator

import httpx
import pytest
import pytest_asyncio
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from backend.app.core import get_settings
from backend.app.main import app
from backend.app.models import Dragon, UserSession


@pytest.fixture(scope="session")
def test_settings() -> None:
    """
    Ensure test environment is configured.

    Tests use a real MongoDB (Atlas) and a dedicated database name so we can
    safely clean collections between tests.
    """

    s = get_settings()
    if not s.mongodb_uri:
        pytest.skip("MONGODB_URI is not set; cannot run integration tests.")

    # Default test DB if not provided.
    if not s.mongodb_db:
        os.environ["MONGODB_DB"] = "pink_sapphire_cove_test"


@pytest_asyncio.fixture(scope="session")
async def beanie_initialized(test_settings: None) -> AsyncIterator[None]:
    s = get_settings()
    client = AsyncIOMotorClient(s.mongodb_uri)
    db = client.get_default_database() if not s.mongodb_db else client[s.mongodb_db]

    await init_beanie(database=db, document_models=[Dragon, UserSession])
    yield
    client.close()


@pytest_asyncio.fixture(autouse=True)
async def clean_collections(beanie_initialized: None) -> AsyncIterator[None]:
    await Dragon.get_motor_collection().delete_many({})
    await UserSession.get_motor_collection().delete_many({})
    yield


@pytest_asyncio.fixture
async def api_client(beanie_initialized: None) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app, lifespan="on")
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

