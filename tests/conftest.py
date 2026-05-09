import asyncio

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient

from app.core import database as db_module
from app.main import app

TEST_DB_NAME = "NPAPI_test"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def clean_db():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client[TEST_DB_NAME]

    original_get_db = db_module.get_db
    db_module.get_db = lambda: db

    await db_module.init_indexes()

    yield

    await client.drop_database(TEST_DB_NAME)
    client.close()
    db_module.get_db = original_get_db


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


@pytest_asyncio.fixture
async def auth_headers(client):
    await client.post(
        "/auth/register",
        json={"username": "testuser", "email": "test@example.com", "password": "secret123"},
    )
    res = await client.post(
        "/auth/login",
        json={"username": "testuser", "password": "secret123"},
    )
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
