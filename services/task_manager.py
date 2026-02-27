import uuid
import httpx
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from agent.browser_agent import BrowserAgent
from config import settings


# In-memory task storage (in production, use Redis or a database)
# TODO: Use Redis for tracking tasks in production to handle restarts and scaling
# TODO: Should we also use a database to store historical task results and analytics? Or just keep recent tasks in Redis with expiration?
tasks: Dict[str, Dict[str, Any]] = {}


class TaskManager:
    """Manages browser automation tasks."""
    
    @staticmethod
    async def execute_task(
        url: str,
        task: str,
        task_id: Optional[str] = None,
        webhook_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute a browser automation task.
        
        Args:
            url: URL to visit
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
            if task_id:
                tasks[task_id] = {
                    "status": "processing",
                    "started_at": datetime.now(timezone.utc).isoformat(),
                    "result": None,
                    "error": None
                }
            
            # Execute the browser task
            async with BrowserAgent(
                ollama_url=settings.OLLAMA_URL,
                model=settings.MODEL,
                headless=settings.HEADLESS
            ) as agent:
                result = await agent.execute_task(url, task)
            
            # Update task status to completed
            if task_id:
                tasks[task_id]["status"] = "completed"
                tasks[task_id]["result"] = [result]
                tasks[task_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
            
            # Send success webhook if provided
            if webhook_url:
                await TaskManager._send_webhook(
                    webhook_url,
                    {
                        "task_id": task_id,
                        "status": "completed",
                        "result": [result]
                    }
                )
            
            return result
            
        except Exception as e:
            error = str(e)
            print(f"❌ Task failed: {e}")
            
            # Update task status with error
            if task_id:
                tasks[task_id]["status"] = "failed"
                tasks[task_id]["error"] = error
                tasks[task_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
            
            # Send error webhook if provided
            if webhook_url:
                await TaskManager._send_webhook(
                    webhook_url,
                    {
                        "task_id": task_id,
                        "status": "failed",
                        "error": error
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
    def create_task(url: str, task: str, webhook_url: str) -> str:
        """Create a new task and return task ID.
        
        Args:
            url: URL to visit
            task: Task description
            webhook_url: Webhook URL for results
            
        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())
        tasks[task_id] = {
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "url": url,
            "task": task,
            "webhook_url": webhook_url
        }
        return task_id
    
    @staticmethod
    def get_task(task_id: str) -> Optional[Dict[str, Any]]:
        """Get task data by ID.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task data or None if not found
        """
        return tasks.get(task_id)
    
    @staticmethod
    def delete_task(task_id: str) -> bool:
        """Delete a task from memory.
        
        Args:
            task_id: Task ID
            
        Returns:
            True if deleted, False if not found
        """
        if task_id in tasks:
            del tasks[task_id]
            return True
        return False
    
    @staticmethod
    def get_task_count() -> int:
        """Get the number of tasks in memory."""
        return len(tasks)
