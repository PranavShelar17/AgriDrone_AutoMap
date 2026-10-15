import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    survey_id: uuid.UUID
    generated_by_user_id: uuid.UUID
    report_number: str
    report_title: str
    blob_uri: str
    file_size_bytes: int
    status: str
    report_parameters: Optional[Dict[str, Any]] = None
    created_at: datetime
    download_url: Optional[str] = None


class ReportListResponse(BaseModel):
    reports: List[ReportResponse]
    total: int
