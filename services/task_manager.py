import uuid
import httpx
import asyncio
import json
import sys

from typing import Dict, Any, Optional
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from agent.llm_client import LLMClient
from agent.playwright_client import PlaywrightClient
from redis.asyncio import Redis

from agent.browser_agent import BrowserAgent
from config import settings


# Thread pool for Windows compatibility (subprocess support)
_executor = ThreadPoolExecutor(max_workers=4)

# Task expiration in seconds (1 hour by default)
TASK_TTL = 3600

def _run_browser_task_sync(url: str, task: str, response_schema: Dict[str, Any], configuration: Dict[str, Any]) -> Dict[str, Any]:
    """
    Synchronous wrapper to run browser task in a new event loop.
    This allows Playwright to work on Windows by running in a separate thread.
    Args:
        url: URL to visit
        task: Task description
        response_schema: Schema for LLM response
        configuration: Additional configuration for the browser agent's LLM and playwright clients
    """
    # On Windows, set the ProactorEventLoop policy before creating the loop
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    # Create new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        async def _execute():
            async with BrowserAgent(
                llm_client=LLMClient(host=settings.OLLAMA_URL, model=settings.MODEL),
                playwright_client=PlaywrightClient(headless=settings.HEADLESS)
            ) as agent:
                return await agent.execute_task(url, task, response_schema=response_schema)
        
        # Run the async task in this thread's event loop
        result = loop.run_until_complete(_execute())
        return result
    finally:
        loop.close()


class TaskManager:
    """Manages browser automation tasks."""
    
    @staticmethod
    async def execute_task(
        redis: Redis,
        url: str,
        task: str,
        response_schema: Dict[str, Any],
        task_id: Optional[str] = None,
        webhook_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute a browser automation task.
        
        Args:
            redis: Redis client
            url: URL to visit
            response_schema: Schema for structured LLM response
            task: Task description
            task_id: Optional task ID for tracking
            webhook_url: Optional webhook URL to POST results to
            
        Returns:
            Task result dictionary
        """
        result = None
        error = None

        try:
            # Update task status to processing
            task_data = {
                "status": "processing",
                "started_at": datetime.now(timezone.utc).isoformat(),
                "result": None,
                "error": None
            }
            await redis.setex(f"task:{task_id}", TASK_TTL, json.dumps(task_data))
            
            # Execute the browser task in thread pool (Windows compatibility)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                _executor,
                _run_browser_task_sync,
                url,
                task,
                response_schema,
            )
            
            # Update task status to completed
            task_data = {
                "status": "completed",
                "result": [result],
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "response_schema": response_schema,
            }
            await redis.setex(f"task:{task_id}", TASK_TTL, json.dumps(task_data))
            
            # Send success webhook if provided
            if webhook_url:
                await TaskManager._send_webhook(
                    webhook_url,
                    {
                        "task_id": task_id,
                        "status": "completed",
                        "result": [result],
                        "response_schema": response_schema,
                    }
                )
            
            return result
            
        except Exception as e:
            error = str(e)
            print(f"❌ Task failed: {e}")
            
            # Update task status with error
            task_data = {
                "status": "failed",
                "error": error,
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "response_schema": response_schema,
            }
            await redis.setex(f"task:{task_id}", TASK_TTL, json.dumps(task_data))
            
            # Send error webhook if provided
            if webhook_url:
                await TaskManager._send_webhook(
                    webhook_url,
                    {
                        "task_id": task_id,
                        "status": "failed",
                        "error": error,
                        "response_schema": response_schema,
                    }
                )
            
            raise
    
    @staticmethod
    async def _send_webhook(webhook_url: str, payload: Dict[str, Any]) -> None:
        """Send webhook notification.
        
        Args:
            webhook_url: URL to POST to
            payload: Data to send
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(webhook_url, json=payload)
            print(f"✅ Webhook sent to {webhook_url}")
        except Exception as e:
            print(f"⚠️  Webhook failed: {e}")
    
    @staticmethod
    async def create_task(redis: Redis, url: str, task: str, webhook_url: str, response_schema: Dict[str, Any]) -> str:
        """Create a new task and return task ID.
        
        Args:
            redis: Redis client
            url: URL to visit
            task: Task description
            webhook_url: Webhook URL for results
            response_schema: Response schema for the task
            
        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())

        task_data = {
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "url": url,
            "task": task,
            "webhook_url": webhook_url,
            "response_schema": response_schema
        }
        await redis.setex(f"task:{task_id}", TASK_TTL, json.dumps(task_data))

        return task_id
    
    @staticmethod
    async def get_task(redis: Redis, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task data by ID.
        
        Args:
            redis: Redis client
            task_id: Task ID
            
        Returns:
            Task data or None if not found
        """
        data = await redis.get(f"task:{task_id}")
        if data:
            return json.loads(data)
        return None
    
    @staticmethod
    async def delete_task(redis: Redis, task_id: str) -> bool:
        """Delete a task from Redis.
        
        Args:
            redis: Redis client
            task_id: Task ID
            
        Returns:
            True if deleted, False if not found
        """
        deleted = await redis.delete(f"task:{task_id}")
        return deleted > 0
    
    @staticmethod
    async def get_task_count(redis: Redis) -> int:
        """Get the number of tasks in Redis.
        
        Args:
            redis: Redis client
            
        Returns:
            Number of tasks
        """
        keys = await redis.keys("task:*")
        return len(keys)
