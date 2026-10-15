from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID
from pydantic import BaseModel, Field


class RecentSurveyItem(BaseModel):
    survey_id: UUID
    survey_code: str
    farm_name: str
    field_name: str
    flight_date: date
    sensor_type: str
    status: str
    files_count: int
    total_bytes: int
    created_at: datetime


class RecentUploadItem(BaseModel):
    file_id: UUID
    survey_id: UUID
    survey_code: str
    original_filename: str
    file_type: str
    file_size_bytes: int
    ingestion_status: str
    workflow_route: str
    created_at: datetime


class RecentFailureItem(BaseModel):
    file_id: UUID
    survey_id: UUID
    survey_code: str
    original_filename: str
    file_size_bytes: int
    validation_errors: List[str]
    created_at: datetime


class DashboardStatsResponse(BaseModel):
    total_farms: int
    total_fields: int
    total_surveys: int
    total_datasets: int
    datasets_awaiting_validation: int
    datasets_validated: int
    datasets_rejected: int
    storage_provider: str
    recent_surveys: List[RecentSurveyItem]
    recent_uploads: List[RecentUploadItem]
    recent_failures: List[RecentFailureItem]
