from fastapi import FastAPI, Depends

from config import settings
from services.task_manager import TaskManager
from dependencies.dependencies import lifespan, Redis
from aliases.global_aliases import RedisDepends


# Initialize FastAPI app with lifespan
app = FastAPI(
    title=settings.TITLE,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    lifespan=lifespan,
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
async def health(r: Redis = RedisDepends):
    """Detailed health check."""
    return {
        "status": "healthy",
        "ollama_url": settings.OLLAMA_URL,
        "model": settings.MODEL,
        "tasks_in_memory": await TaskManager.get_task_count(r)
    }

# Include task routes from router
from routes.tasks_controller import router as tasks_router

app.include_router(tasks_router)
