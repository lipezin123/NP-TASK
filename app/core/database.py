from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings

_client: AsyncIOMotorClient | None = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.MONGODB_URI)
    return _client


def get_db():
    return get_client()[settings.MONGODB_DB_NAME]


async def close_client() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None


async def init_indexes() -> None:
    db = get_db()
    await db.users.create_index("username", unique=True)
    await db.users.create_index("email", unique=True)
    await db.tasks.create_index("owner_id")
    await db.tasks.create_index("created_at")
    await db.ip_registrations.create_index("ip", unique=True)
    await db.rate_limits.create_index("ip")
    await db.rate_limits.create_index(
        "expires_at", expireAfterSeconds=0
    )
