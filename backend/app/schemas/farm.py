from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class FieldBase(BaseModel):
    field_name: str = Field(..., min_length=1, max_length=150, description="Field designation name")
    crop_type: Optional[str] = Field(default=None, max_length=100, description="Planted crop species")
    area_hectares: Optional[float] = Field(default=None, ge=0.01, le=100000.0, description="Field area in hectares")
    boundary_geojson: Optional[Dict[str, Any]] = Field(default=None, description="GeoJSON Polygon boundary")


class FieldCreate(FieldBase):
    farm_id: Optional[UUID] = Field(default=None, description="Associated Farm ID (can be in path)")


class FieldUpdate(BaseModel):
    field_name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    crop_type: Optional[str] = Field(default=None, max_length=100)
    area_hectares: Optional[float] = Field(default=None, ge=0.01)
    boundary_geojson: Optional[Dict[str, Any]] = None


class FieldResponse(FieldBase):
    id: UUID
    farm_id: UUID
    surveys_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class FarmBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Farm or estate name")
    village: Optional[str] = Field(default=None, max_length=100)
    district: Optional[str] = Field(default=None, max_length=100)
    state: Optional[str] = Field(default=None, max_length=100)
    boundary_geojson: Optional[Dict[str, Any]] = Field(default=None, description="GeoJSON Polygon boundary")


class FarmCreate(FarmBase):
    owner_id: Optional[UUID] = Field(default=None, description="Owner User ID")


class FarmUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    village: Optional[str] = Field(default=None, max_length=100)
    district: Optional[str] = Field(default=None, max_length=100)
    state: Optional[str] = Field(default=None, max_length=100)
    boundary_geojson: Optional[Dict[str, Any]] = None


class FarmResponse(FarmBase):
    id: UUID
    owner_id: UUID
    fields_count: int = 0
    surveys_count: int = 0
    created_at: datetime
    fields: Optional[List[FieldResponse]] = None

    class Config:
        from_attributes = True


class FarmListResponse(BaseModel):
    items: List[FarmResponse]
    total: int
    skip: int
    limit: int
