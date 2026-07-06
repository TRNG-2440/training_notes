# the API functionality
from fastapi import APIRouter, status, HTTPException

# the task object(s)
from ..models.task import TaskCreate, TaskUpdate, TaskOut

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    responses={404: {"description": "Task not found"}},
    )

# ---------- Pseudo - DB ----------
_TASKSDB: dict[int, dict] = {}
_next_id: int = 1

def get_or_404(task_id: int) -> dict:
    task = _TASKSDB.get(task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
            )
    return task


# ----------- Routes --------------

# Get
# Get 1 or many
@router.get(
    "",
    response_model=list[TaskOut],
    summary="List of tasks"
    )
# def get_all()
#     return list(_TASKDB.values())
def get_all_paginated(done: bool | None = None, limit: int = 25, offset: int = 0):
    rows = list(_TASKSDB.values())
    if done is not None:
        rows = [ r for r in rows if r["done"] == done]
    return rows[offset : offset + limit]

# Get 1 by id
@router.get(
    "/{taskc_id}",
    response_model=TaskOut,
    summary="Get task by id"
    )
def get_task(task_id: int):
    return get_or_404(task_id)


# Post - Create
@router.post(
    "",
    response_model=TaskOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a task"
    )
def create_task(payload: TaskCreate):
    global _next_id
    record = {"id": _next_id, **payload.model_dump()}
    _TASKSDB[_next_id] = record
    _next_id +=1
    return record

# Put
@router.put(
    "/{task_id}",
    response_model=TaskOut,
    summary="Replace a task")
def update_by_id(task_id: int, payload: TaskUpdate):
    get_or_404(task_id) #validate the record actually exists!
    record = {"id":task_id, **payload.model_dump()}
    _TASKSDB[task_id] = record
    return record

# Delete
@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task"
    )
def delete_task(task_id: int):
    get_or_404(task_id)
    del _TASKSDB[task_id]
    return None
