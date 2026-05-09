from datetime import datetime, timezone
from typing import Any

from bson import ObjectId


class User:
    def __init__(
        self,
        username: str,
        email: str,
        hashed_password: str,
        created_at: datetime | None = None,
        _id: ObjectId | None = None,
    ):
        self.id = str(_id) if _id else None
        self.username = username
        self.email = email
        self.hashed_password = hashed_password
        self.created_at = created_at or datetime.now(timezone.utc)

    @classmethod
    def from_mongo(cls, doc: dict[str, Any]) -> "User":
        obj = cls.__new__(cls)
        obj.id = str(doc["_id"])
        obj.username = doc["username"]
        obj.email = doc["email"]
        obj.hashed_password = doc["hashed_password"]
        obj.created_at = doc.get("created_at", datetime.now(timezone.utc))
        return obj

    def to_mongo(self) -> dict[str, Any]:
        return {
            "username": self.username,
            "email": self.email,
            "hashed_password": self.hashed_password,
            "created_at": self.created_at,
        }
