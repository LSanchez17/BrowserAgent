"""
API request and response schemas.
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class BrowserAgentRequest(BaseModel):
    """Request model for browser agent endpoint."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "url": "https://example.com",
                "task": "Find the main heading and describe the page purpose",
                "webhook_url": "https://your-service.com/webhook/callback"
            }
        }
    )
    
    url: str = Field(..., description="URL to visit")
    task: str = Field(..., description="Description of what to do")
    webhook_url: Optional[str] = Field(None, description="Optional webhook URL for async execution")
    response_schema: Dict[str, Any] = Field(
        ...,
        description="JSON-like schema describing desired response shape"
    )


class BrowserAgentResponse(BaseModel):
    """Response model for browser agent endpoint."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "result": [
                    {
                        "url": "https://example.com",
                        "title": "Example Domain",
                        "task": "Find the main heading",
                        "result": "The main heading is 'Example Domain'...",
                        "status": "completed"
                    }
                ],
                "status": "completed"
            }
        }
    )
    
    result: list[Dict[str, Any]] = Field(..., description="List of result objects")
    task_id: Optional[str] = Field(None, description="Task ID for async execution")
    status: str = Field(..., description="Status of the task")


class TaskStatusResponse(BaseModel):
    """Response model for task status check."""
    task_id: str
    status: str
    result: Optional[list[Dict[str, Any]]] = None
    error: Optional[str] = None
