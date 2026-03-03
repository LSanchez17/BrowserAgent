from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from redis.asyncio import Redis

from schemas.schemas import BrowserAgentRequest, BrowserAgentResponse, TaskStatusResponse
from services.task_manager import TaskManager
from dependencies.dependencies import get_redis
from aliases.global_aliases import RedisDepends

router = APIRouter()

@router.post("/tasks", response_model=BrowserAgentResponse)
async def create_tasks_endpoint(
    request: BrowserAgentRequest,
    background_tasks: BackgroundTasks,
    redis: Redis = RedisDepends
):
    url = request.url
    task = request.task
    webhook_url = request.webhook_url

    task_id = await TaskManager.create_task(redis, url=url, task=task, webhook_url=webhook_url)

    background_tasks.add_task(
        TaskManager.execute_task,
        redis,
        url,
        task,
        task_id,
        webhook_url,
    )

    return BrowserAgentResponse(result=[], task_id=task_id, status="pending")


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str, redis: Redis = RedisDepends):
    task_data = await TaskManager.get_task(redis, task_id)

    if not task_data:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskStatusResponse(
        task_id=task_id,
        status=task_data["status"],
        result=task_data.get("result"),
        error=task_data.get("error"),
    )


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str, redis: Redis = RedisDepends):
    if not await TaskManager.delete_task(redis, task_id):
        raise HTTPException(status_code=404, detail="Task not found")

    return {"message": "Task deleted", "task_id": task_id}
