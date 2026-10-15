from typing import List, Dict, Any, Optional
import uuid
from pydantic import BaseModel, Field


class GeoJSONGeometry(BaseModel):
    type: str
    coordinates: Any


class FieldBoundaryGeoJSON(BaseModel):
    type: str = "Feature"
    id: uuid.UUID
    geometry: Optional[GeoJSONGeometry] = None
    properties: Dict[str, Any] = Field(default_factory=dict)
    bbox: Optional[List[float]] = None  # [minX, minY, maxX, maxY]
    centroid: Optional[List[float]] = None  # [lon, lat]


class SurveyCoverageGeoJSON(BaseModel):
    type: str = "Feature"
    id: uuid.UUID
    geometry: Optional[GeoJSONGeometry] = None
    properties: Dict[str, Any] = Field(default_factory=dict)
    bbox: Optional[List[float]] = None


class LegendStop(BaseModel):
    value: float
    color: str  # Hex or rgba string
    label: str


class MapLegend(BaseModel):
    title: str
    unit: str
    colormap_type: str  # "CONTINUOUS", "CATEGORICAL", "RGB"
    min_value: float
    max_value: float
    nodata_color: str = "rgba(0,0,0,0)"
    stops: List[LegendStop] = Field(default_factory=list)


class MapLayerVisualization(BaseModel):
    product_id: uuid.UUID
    product_type: str
    survey_id: uuid.UUID
    field_id: Optional[uuid.UUID] = None
    farm_id: Optional[uuid.UUID] = None
    crs_epsg: str
    is_cog: bool = True
    bounds: List[float]  # [minLon, minLat, maxLon, maxLat] in EPSG:4326
    center: List[float]  # [lon, lat] in EPSG:4326
    tile_url_template: str  # e.g., "/api/v1/maps/tiles/{product_id}/{z}/{x}/{y}.png"
    legend: MapLegend
    statistical_summary: Optional[Dict[str, Any]] = None


class MapProductListItem(BaseModel):
    id: uuid.UUID
    survey_id: uuid.UUID
    survey_code: str
    farm_name: str
    field_name: str
    product_type: str
    display_name: str
    band_count: int
    crs_epsg: str
    resolution_cm_px: Optional[float] = None
    is_cog: bool
    is_published: bool
    created_at: str
    has_raster_file: bool


class PointProbeResponse(BaseModel):
    product_id: uuid.UUID
    lat: float
    lon: float
    value: Optional[float] = None
    unit: str
    is_valid: bool
    description: str


class ZonalDistributionItem(BaseModel):
    zone_name: str
    min_val: float
    max_val: float
    area_hectares: float
    area_percentage: float
    color: str


class DiagnosticSummaryResponse(BaseModel):
    product_id: uuid.UUID
    product_type: str
    display_name: str
    survey_id: uuid.UUID
    survey_code: str
    field_name: str
    farm_name: str
    crop_type: Optional[str] = None
    crs_epsg: str
    resolution_cm_px: Optional[float] = None
    valid_pixel_count: int
    nodata_pixel_count: int
    total_pixel_count: int
    valid_percentage: float
    covered_area_hectares: float
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    mean_value: Optional[float] = None
    std_value: Optional[float] = None
    median_value: Optional[float] = None
    unit: str
    zonal_distribution: List[ZonalDistributionItem] = Field(default_factory=list)
    scientific_warnings: List[str] = Field(default_factory=list)
    analytical_limitations: List[str] = Field(default_factory=list)


class ComparisonCompatibilityResponse(BaseModel):
    product_a_id: uuid.UUID
    product_b_id: uuid.UUID
    is_compatible: bool
    spatial_overlap_percentage: float
    reason: str
    recommendation: str
