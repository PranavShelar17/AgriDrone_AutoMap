from uuid import UUID
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator


class EligibleDatasetItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    file_id: UUID
    survey_id: UUID
    survey_code: str
    farm_name: Optional[str] = None
    field_name: Optional[str] = None
    original_filename: str
    file_type: str
    file_size_bytes: int
    ingestion_status: str
    workflow_route: str
    is_eligible: bool
    ineligibility_reason: Optional[str] = None
    photo_count_estimate: Optional[int] = None
    camera_model: Optional[str] = None
    created_at: datetime


class EligibleDatasetsResponse(BaseModel):
    items: List[EligibleDatasetItem]
    total: int
    eligible_count: int
    ineligible_count: int


class PhotogrammetryTaskCreate(BaseModel):
    survey_id: UUID
    source_file_id: Optional[UUID] = None
    resolution_preset: str = Field(default="HIGH_RES", description="Resolution preset: FAST | HIGH_RES | CUSTOM")
    custom_resolution_cm: Optional[float] = Field(default=None, ge=0.5, le=100.0, description="Custom GSD in cm/pixel")
    generate_dsm: bool = Field(default=True, description="Generate Digital Surface Model")
    generate_dtm: bool = Field(default=True, description="Generate Digital Terrain Model")
    radiometric_calibration: bool = Field(default=False, description="Enable radiometric panel calibration")
    feature_quality: str = Field(default="high", description="OpenSfM feature quality: ultra | high | medium | low | lowest")
    pc_quality: str = Field(default="medium", description="Point cloud quality: ultra | high | medium | low | lowest")

    @field_validator("resolution_preset")
    @classmethod
    def validate_preset(cls, v: str) -> str:
        upper = v.upper()
        if upper not in ("FAST", "HIGH_RES", "CUSTOM"):
            raise ValueError("resolution_preset must be one of: FAST, HIGH_RES, CUSTOM")
        return upper

    @field_validator("feature_quality")
    @classmethod
    def validate_fq(cls, v: str) -> str:
        lower = v.lower()
        if lower not in ("ultra", "high", "medium", "low", "lowest"):
            raise ValueError("feature_quality must be ultra, high, medium, low, or lowest")
        return lower

    @field_validator("pc_quality")
    @classmethod
    def validate_pq(cls, v: str) -> str:
        lower = v.lower()
        if lower not in ("ultra", "high", "medium", "low", "lowest"):
            raise ValueError("pc_quality must be ultra, high, medium, low, or lowest")
        return lower


class PhotogrammetryTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    task_id: UUID
    survey_id: UUID
    survey_code: Optional[str] = None
    source_file_id: Optional[UUID] = None
    source_filename: Optional[str] = None
    webodm_task_uuid: Optional[str] = None
    resolution_preset: str
    generate_dsm: bool
    generate_dtm: bool
    radiometric_calibration: bool
    options: Optional[Dict[str, Any]] = None
    status: str
    progress_percent: int
    current_stage: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    generated_products_count: int = 0


class PhotogrammetryTaskListResponse(BaseModel):
    items: List[PhotogrammetryTaskResponse]
    total: int
    skip: int
    limit: int


class TaskLogItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: UUID
    log_level: str
    message: str
    logged_at: datetime


class TaskLogsResponse(BaseModel):
    task_id: UUID
    logs: List[TaskLogItem]
    total_lines: int


class ClusterStatusResponse(BaseModel):
    cluster_status: str
    is_connected: bool
    api_url: str
    engine: str
    active_nodes: int
    total_nodes: int
    available_ram_gb: Optional[float] = None
    details: str
    error_message: Optional[str] = None
    timestamp: str


class ArtifactItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: UUID
    survey_id: UUID
    source_task_id: Optional[UUID] = None
    product_type: str
    original_filename: str
    blob_uri: str
    is_cog: bool
    band_count: int
    crs_epsg: str
    resolution_cm_px: Optional[float] = None
    created_at: datetime


class ArtifactListResponse(BaseModel):
    task_id: UUID
    survey_id: UUID
    items: List[ArtifactItem]
    total: int


class TaskActionResponse(BaseModel):
    task_id: UUID
    status: str
    message: str
