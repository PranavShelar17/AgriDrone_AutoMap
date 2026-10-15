"""Pydantic schemas for Phase 7 Algorithms, Raster Analytics & Multi-Map Generation."""

from uuid import UUID
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field, ConfigDict, field_validator


class AlgorithmSpecResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    display_name: str
    required_sensor: str
    formula: str
    required_bands: List[str]
    expected_range: Tuple[float, float]
    description: str
    parameters: Optional[Dict[str, Any]] = None


class BandSummarySchema(BaseModel):
    band_index: int
    data_type: str
    nodata_value: Optional[float] = None
    min_value: float
    max_value: float
    mean_value: float
    std_value: float
    description: Optional[str] = None


class RasterInspectionResponse(BaseModel):
    source_id: UUID
    source_type: str  # "MAP_PRODUCT" or "SURVEY_FILE"
    survey_id: UUID
    survey_code: Optional[str] = None
    farm_name: Optional[str] = None
    field_name: Optional[str] = None
    width: int
    height: int
    band_count: int
    crs_epsg: Optional[str] = None
    bounds: Tuple[float, float, float, float]
    gsd_cm: float
    detected_sensor: str
    radiometric_type: str
    calibration_notes: List[str]
    suggested_band_mapping: Dict[str, int]
    supported_algorithms: List[str]
    bands: List[BandSummarySchema]


class EligibleRasterItem(BaseModel):
    source_id: UUID
    source_type: str  # "MAP_PRODUCT" or "SURVEY_FILE"
    survey_id: UUID
    survey_code: str
    farm_name: Optional[str] = None
    field_name: Optional[str] = None
    filename: str
    product_type: str
    band_count: int
    crs_epsg: str
    resolution_cm_px: Optional[float] = None
    detected_sensor: str
    is_eligible: bool
    ineligibility_reason: Optional[str] = None
    created_at: datetime


class EligibleRastersResponse(BaseModel):
    items: List[EligibleRasterItem]
    total: int
    eligible_count: int
    ineligible_count: int


class BandMappingValidateRequest(BaseModel):
    band_count: int
    mapping: Dict[str, int]
    algorithm_codes: List[str]


class BandMappingValidateResponse(BaseModel):
    is_valid: bool
    per_algorithm_status: Dict[str, Dict[str, Any]]
    overall_message: Optional[str] = None


class AlgorithmJobCreate(BaseModel):
    algorithm_code: str
    parameters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional algorithm parameters, e.g. {'L': 0.5} for SAVI",
    )

    @field_validator("algorithm_code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        upper = v.upper().strip()
        if upper not in ("NDVI", "NDRE", "GNDVI", "SAVI", "VARI", "GLI"):
            raise ValueError(f"Unsupported algorithm code: {upper}")
        return upper


class AlgorithmBatchCreateRequest(BaseModel):
    source_id: UUID = Field(..., description="ID of input MapProduct or SurveyFile GeoTIFF")
    source_type: str = Field(default="MAP_PRODUCT", description="'MAP_PRODUCT' or 'SURVEY_FILE'")
    band_mapping: Dict[str, int] = Field(..., description="Spectral channel mapping, e.g. {'NIR': 5, 'Red': 3}")
    algorithms: List[AlgorithmJobCreate] = Field(..., min_length=1, description="List of algorithms to generate")


class AlgorithmJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: UUID
    batch_id: Optional[UUID] = None
    algorithm_code: str
    algorithm_name: Optional[str] = None
    input_product_id: UUID
    status: str
    current_stage: Optional[str] = None
    progress_percent: int
    error_message: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    output_product_id: Optional[UUID] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class AlgorithmBatchResponse(BaseModel):
    batch_id: UUID
    survey_id: UUID
    input_product_id: UUID
    total_jobs: int
    completed_jobs: int
    failed_jobs: int
    in_progress_jobs: int
    status: str  # QUEUED | RUNNING | COMPLETED | PARTIALLY_COMPLETED | FAILED
    jobs: List[AlgorithmJobResponse]


class ZonalStatItem(BaseModel):
    zone_name: str
    min_val: float
    max_val: float
    area_hectares: float
    area_percentage: float


class MapProductDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: UUID
    survey_id: UUID
    source_job_id: Optional[UUID] = None
    product_type: str
    blob_uri: str
    access_url: str
    is_cog: bool
    band_count: int
    crs_epsg: str
    resolution_cm_px: Optional[float] = None
    statistical_summary: Optional[Dict[str, Any]] = None
    zonal_statistics: List[ZonalStatItem] = []
    created_at: datetime
