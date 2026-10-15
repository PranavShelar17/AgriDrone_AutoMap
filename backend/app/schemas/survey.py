from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID
from pydantic import BaseModel, Field


class SurveyBase(BaseModel):
    survey_code: Optional[str] = Field(default=None, max_length=50, description="Unique survey mission code (auto-generated if empty)")
    flight_date: date = Field(..., description="Flight mission capture date (YYYY-MM-DD)")
    drone_model: Optional[str] = Field(default="DJI Mavic 3 Enterprise", max_length=100)
    sensor_type: str = Field(default="RGB", max_length=50, description="Sensor classification (RGB or MULTISPECTRAL)")
    flight_altitude_m: Optional[float] = Field(default=80.0, ge=5.0, le=500.0, description="Flight AGL altitude in meters")
    coverage_geojson: Optional[Dict[str, Any]] = Field(default=None, description="Flight perimeter polygon GeoJSON")


class SurveyCreate(SurveyBase):
    field_id: UUID = Field(..., description="Target agricultural field ID")


class SurveyUpdate(BaseModel):
    survey_code: Optional[str] = Field(default=None, max_length=50)
    flight_date: Optional[date] = None
    drone_model: Optional[str] = None
    sensor_type: Optional[str] = None
    flight_altitude_m: Optional[float] = None
    status: Optional[str] = None
    coverage_geojson: Optional[Dict[str, Any]] = None


class SurveyFileBrief(BaseModel):
    id: UUID
    original_filename: str
    file_type: str
    file_size_bytes: int
    mime_type: str
    ingestion_status: str
    created_at: datetime
    validation_metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class SurveyResponse(SurveyBase):
    id: UUID
    field_id: UUID
    farm_name: Optional[str] = None
    field_name: Optional[str] = None
    status: str
    created_at: datetime
    files_count: int = 0
    total_bytes: int = 0

    class Config:
        from_attributes = True


class SurveyDetailResponse(SurveyResponse):
    files: List[SurveyFileBrief] = []


class SurveyListResponse(BaseModel):
    items: List[SurveyResponse]
    total: int
    skip: int
    limit: int
