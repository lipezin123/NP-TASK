from datetime import datetime, timezone
from enum import Enum
from typing import Any

from bson import ObjectId


class TaskStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    done = "done"


class Task:
    def __init__(
        self,
        title: str,
        owner_id: str,
        description: str | None = None,
        status: TaskStatus = TaskStatus.pending,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        _id: ObjectId | None = None,
    ):
        self.id = str(_id) if _id else None
        self.title = title
        self.description = description
        self.status = status
        self.owner_id = owner_id
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)

    @classmethod
    def from_mongo(cls, doc: dict[str, Any]) -> "Task":
        obj = cls.__new__(cls)
        obj.id = str(doc["_id"])
        obj.title = doc["title"]
        obj.description = doc.get("description")
        obj.status = TaskStatus(doc.get("status", "pending"))
        obj.owner_id = doc["owner_id"]
        obj.created_at = doc.get("created_at", datetime.now(timezone.utc))
        obj.updated_at = doc.get("updated_at", datetime.now(timezone.utc))
        return obj

    def to_mongo(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "owner_id": self.owner_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
