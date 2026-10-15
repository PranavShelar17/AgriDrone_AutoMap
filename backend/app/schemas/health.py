from typing import Dict, Literal
from datetime import datetime
from pydantic import BaseModel, Field


class ComponentStatus(BaseModel):
    status: Literal["healthy", "unhealthy", "disabled"]
    latency_ms: float
    details: str = ""


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded", "down"]
    version: str
    environment: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ReadinessResponse(BaseModel):
    status: Literal["ready", "not_ready"]
    components: Dict[str, ComponentStatus]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
