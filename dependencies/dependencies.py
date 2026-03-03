from contextlib import asynccontextmanager
from fastapi import FastAPI
from redis.asyncio import Redis

from config import settings

# Global Redis client
redis_client: Redis = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown events."""
    global redis_client
    redis_client = Redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )
    
    print(f"✅ Connected to Redis: {settings.REDIS_URL}")

    yield

    await redis_client.close()
    print("👋 Closed Redis connection")


async def get_redis() -> Redis:
    """Dependency to get Redis client."""
    return redis_client
