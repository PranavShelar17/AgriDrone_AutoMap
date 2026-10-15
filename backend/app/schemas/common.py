from typing import Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ErrorDetails(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None


class ErrorResponse(BaseModel):
    error: ErrorDetails


class StandardMessageResponse(BaseModel):
    status: str = "success"
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
