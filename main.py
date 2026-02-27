from fastapi import FastAPI, BackgroundTasks, HTTPException

from schemas.schemas import BrowserAgentRequest, BrowserAgentResponse, TaskStatusResponse
from config import settings
from services.task_manager import TaskManager


# Initialize FastAPI app
app = FastAPI(
    title=settings.TITLE,
    description=settings.DESCRIPTION,
    version=settings.VERSION
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": settings.TITLE,
        "status": "running",
        "version": settings.VERSION
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "ollama_url": settings.OLLAMA_URL,
        "model": settings.MODEL,
        "tasks_in_memory": TaskManager.get_task_count()
    }


@app.post("/browser_agent", response_model=BrowserAgentResponse)
async def browser_agent_endpoint(
    request: BrowserAgentRequest,
    background_tasks: BackgroundTasks
):
    """
    Execute a browser automation task.
    
    **Synchronous mode** (no webhook_url):
    - Executes task immediately and returns results
    - May take 10-30+ seconds depending on task complexity
    - Risk of timeout for very long tasks
    
    **Asynchronous mode** (with webhook_url):
    - Returns immediately with task_id
    - Executes task in background
    - POSTs results to webhook_url when complete
    - Use /task/{task_id} endpoint to check status
    """
    
    # Asynchronous mode with webhook
    if request.webhook_url:
        task_id = TaskManager.create_task(
            url=request.url,
            task=request.task,
            webhook_url=request.webhook_url
        )
        
        # Schedule background execution
        background_tasks.add_task(
            TaskManager.execute_task,
            request.url,
            request.task,
            task_id,
            request.webhook_url
        )
        
        return BrowserAgentResponse(
            result=[],
            task_id=task_id,
            status="pending"
        )
    
    # Synchronous mode - execute immediately
    else:
        try:
            result = await TaskManager.execute_task(request.url, request.task)
            return BrowserAgentResponse(
                result=[result],
                status="completed"
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    Get the status of an asynchronous task.
    
    Use this endpoint to poll for task completion when using async mode.
    """
    task_data = TaskManager.get_task(task_id)
    if not task_data:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return TaskStatusResponse(
        task_id=task_id,
        status=task_data["status"],
        result=task_data.get("result"),
        error=task_data.get("error")
    )


@app.delete("/task/{task_id}")
async def delete_task(task_id: str):
    """Delete a task from memory."""
    if not TaskManager.delete_task(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {"message": "Task deleted", "task_id": task_id}
