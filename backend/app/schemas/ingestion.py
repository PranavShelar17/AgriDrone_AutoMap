from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class FileUploadResponse(BaseModel):
    file_id: UUID
    survey_id: UUID
    original_filename: str
    file_type: str
    file_size_bytes: int
    mime_type: str
    blob_uri: str
    md5_checksum: Optional[str] = None
    ingestion_status: str
    workflow_route: str
    validation_metadata: Optional[Dict[str, Any]] = None
    validation_errors: List[str] = []
    created_at: datetime

    class Config:
        from_attributes = True


class SurveyFileListResponse(BaseModel):
    survey_id: UUID
    items: List[FileUploadResponse]
    total_files: int
    total_bytes: int
    validated_count: int
    rejected_count: int
