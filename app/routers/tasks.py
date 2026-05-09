from fastapi import APIRouter, Depends, HTTPException, status

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.rate_limiter import enforce_rate_limit
from app.schemas.task import TaskCreate, TaskListResponse, TaskResponse, TaskUpdate
from app.services import task_service

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    dependencies=[Depends(enforce_rate_limit)],
)


@router.get("", response_model=TaskListResponse)
async def list_tasks(current_user=Depends(get_current_user)):
    db = get_db()
    total, items = await task_service.get_all(db, current_user.id)
    return TaskListResponse(
        total=total,
        items=[
            TaskResponse(
                id=t.id,
                title=t.title,
                description=t.description,
                status=t.status,
                owner_id=t.owner_id,
                created_at=t.created_at,
                updated_at=t.updated_at,
            )
            for t in items
        ],
    )


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(payload: TaskCreate, current_user=Depends(get_current_user)):
    db = get_db()
    task = await task_service.create(db, payload, current_user.id)
    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status,
        owner_id=task.owner_id,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, current_user=Depends(get_current_user)):
    db = get_db()
    task = await task_service.get_by_id(db, task_id, current_user.id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tarefa com id {task_id} não encontrada.",
        )
    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status,
        owner_id=task.owner_id,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.patch("/{task_id}/status", response_model=TaskResponse)
async def update_task_status(
    task_id: str,
    payload: TaskUpdate,
    current_user=Depends(get_current_user),
):
    db = get_db()
    task = await task_service.get_by_id(db, task_id, current_user.id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tarefa com id {task_id} não encontrada.",
        )
    task = await task_service.update_status(db, task, payload)
    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status,
        owner_id=task.owner_id,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: str, current_user=Depends(get_current_user)):
    db = get_db()
    task = await task_service.get_by_id(db, task_id, current_user.id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tarefa com id {task_id} não encontrada.",
        )
    await task_service.delete(db, task)
