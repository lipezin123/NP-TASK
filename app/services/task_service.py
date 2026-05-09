from datetime import datetime, timezone

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate


async def get_all(db: AsyncIOMotorDatabase, owner_id: str) -> tuple[int, list[Task]]:
    cursor = db.tasks.find({"owner_id": owner_id}).sort("created_at", -1)
    docs = await cursor.to_list(length=None)
    return len(docs), [Task.from_mongo(d) for d in docs]


async def get_by_id(db: AsyncIOMotorDatabase, task_id: str, owner_id: str) -> Task | None:
    try:
        oid = ObjectId(task_id)
    except Exception:
        return None
    doc = await db.tasks.find_one({"_id": oid, "owner_id": owner_id})
    return Task.from_mongo(doc) if doc else None


async def create(db: AsyncIOMotorDatabase, payload: TaskCreate, owner_id: str) -> Task:
    task = Task(
        title=payload.title,
        description=payload.description,
        status=payload.status,
        owner_id=owner_id,
    )
    result = await db.tasks.insert_one(task.to_mongo())
    task.id = str(result.inserted_id)
    return task


async def update_status(db: AsyncIOMotorDatabase, task: Task, payload: TaskUpdate) -> Task:
    now = datetime.now(timezone.utc)
    await db.tasks.update_one(
        {"_id": ObjectId(task.id)},
        {"$set": {"status": payload.status.value, "updated_at": now}},
    )
    task.status = payload.status
    task.updated_at = now
    return task


async def delete(db: AsyncIOMotorDatabase, task: Task) -> None:
    await db.tasks.delete_one({"_id": ObjectId(task.id)})
