from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user import UserCreate


async def get_by_username(db: AsyncIOMotorDatabase, username: str) -> User | None:
    doc = await db.users.find_one({"username": username})
    return User.from_mongo(doc) if doc else None


async def get_by_email(db: AsyncIOMotorDatabase, email: str) -> User | None:
    doc = await db.users.find_one({"email": email})
    return User.from_mongo(doc) if doc else None


async def create(db: AsyncIOMotorDatabase, payload: UserCreate) -> User:
    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    result = await db.users.insert_one(user.to_mongo())
    user.id = str(result.inserted_id)
    return user


async def authenticate(db: AsyncIOMotorDatabase, username: str, password: str) -> User | None:
    user = await get_by_username(db, username)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


async def ip_already_registered(db: AsyncIOMotorDatabase, ip: str) -> bool:
    doc = await db.ip_registrations.find_one({"ip": ip})
    return doc is not None


async def register_ip(db: AsyncIOMotorDatabase, ip: str) -> None:
    await db.ip_registrations.insert_one({"ip": ip})
