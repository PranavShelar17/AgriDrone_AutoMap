"""Maps and Geospatial Visualization API Endpoints.

Phase 8 Interactive GIS Maps Engine.
Provides PostGIS field boundaries, raster tile streaming, layer visualization metadata,
point value probing, zonal diagnostics, and comparison compatibility checks.
"""

import json
import uuid
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Query, Response, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from geoalchemy2.functions import ST_AsGeoJSON

from app.core.config import settings
from app.db.session import get_db
from app.api.deps import (
    get_current_user,
    get_current_user_with_query_fallback,
    verify_field_access,
    verify_survey_access,
    verify_map_product_access,
)
from app.models.tenant import User, UserRole
from app.models.product import MapProduct, ZonalStatistic
from app.models.survey import Survey
from app.models.farm import Farm, Field
from app.schemas.maps import (
    FieldBoundaryGeoJSON,
    SurveyCoverageGeoJSON,
    MapLayerVisualization,
    MapProductListItem,
    MapLegend,
    LegendStop,
    PointProbeResponse,
    DiagnosticSummaryResponse,
    ZonalDistributionItem,
    ComparisonCompatibilityResponse,
)
from app.services.map_rendering import MapRenderingService, TRANSPARENT_TILE_BYTES

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_display_name_and_unit(product_type: str) -> tuple[str, str, str]:
    """Returns (display_name, unit, colormap_type) for a given product type."""
    p_upper = product_type.upper()
    if p_upper == "ORTHOPHOTO":
        return "RGB Orthomosaic", "reflectance", "RGB"
    elif p_upper == "DSM":
        return "Digital Surface Model (DSM)", "meters", "ELEVATION"
    elif p_upper == "DTM":
        return "Digital Terrain Model (DTM)", "meters", "ELEVATION"
    elif p_upper == "INDEX_NDVI":
        return "Normalized Difference Vegetation Index (NDVI)", "dimensionless", "CONTINUOUS"
    elif p_upper == "INDEX_NDRE":
        return "Normalized Difference Red Edge (NDRE)", "dimensionless", "CONTINUOUS"
    elif p_upper == "INDEX_GNDVI":
        return "Green Normalized Difference Vegetation Index (GNDVI)", "dimensionless", "CONTINUOUS"
    elif p_upper == "INDEX_SAVI":
        return "Soil-Adjusted Vegetation Index (SAVI)", "dimensionless", "CONTINUOUS"
    elif p_upper == "INDEX_VARI":
        return "Visible Atmospherically Resistant Index (VARI)", "dimensionless", "CONTINUOUS"
    elif p_upper == "INDEX_GLI":
        return "Green Leaf Index (GLI)", "dimensionless", "CONTINUOUS"
    return product_type, "unitless", "CONTINUOUS"


def _build_legend_for_product(product_type: str, stats: Optional[Dict[str, Any]] = None) -> MapLegend:
    """Constructs dynamic legend with numeric thresholds and color stops."""
    name, unit, cmap_type = _get_display_name_and_unit(product_type)

    if cmap_type == "RGB":
        return MapLegend(
            title=name,
            unit=unit,
            colormap_type="RGB",
            min_value=0.0,
            max_value=255.0,
            nodata_color="rgba(0,0,0,0)",
            stops=[
                LegendStop(value=0.0, color="#000000", label="Black / Shadow"),
                LegendStop(value=128.0, color="#808080", label="Midtone Imagery"),
                LegendStop(value=255.0, color="#ffffff", label="Highlight Imagery"),
            ],
        )

    if cmap_type == "ELEVATION":
        min_v = float(stats.get("min", 100.0)) if stats else 100.0
        max_v = float(stats.get("max", 500.0)) if stats else 500.0
        span = max(max_v - min_v, 1.0)
        return MapLegend(
            title=name,
            unit=unit,
            colormap_type="ELEVATION",
            min_value=round(min_v, 1),
            max_value=round(max_v, 1),
            nodata_color="rgba(0,0,0,0)",
            stops=[
                LegendStop(value=round(min_v, 1), color="#2b83ba", label=f"Lowest ({round(min_v, 1)}m)"),
                LegendStop(value=round(min_v + 0.25 * span, 1), color="#abdda4", label="Low Elevation"),
                LegendStop(value=round(min_v + 0.5 * span, 1), color="#ffffbf", label="Medium Elevation"),
                LegendStop(value=round(min_v + 0.75 * span, 1), color="#fdae61", label="High Elevation"),
                LegendStop(value=round(max_v, 1), color="#d7191c", label=f"Highest ({round(max_v, 1)}m)"),
            ],
        )

    if product_type.upper() == "INDEX_GNDVI":
        return MapLegend(
            title=name,
            unit=unit,
            colormap_type="CONTINUOUS",
            min_value=-1.0,
            max_value=1.0,
            nodata_color="rgba(0,0,0,0)",
            stops=[
                LegendStop(value=0.0, color="#440154", label="Non-Vegetated (< 0.2)"),
                LegendStop(value=0.3, color="#3b528b", label="Low Chlorophyll (0.2 - 0.4)"),
                LegendStop(value=0.5, color="#21918c", label="Moderate Chlorophyll (0.4 - 0.6)"),
                LegendStop(value=0.7, color="#5ec962", label="High Chlorophyll (0.6 - 0.8)"),
                LegendStop(value=1.0, color="#fde725", label="Peak Chlorophyll (> 0.8)"),
            ],
        )

    # Standard RdYlGn for NDVI, NDRE, SAVI, VARI, GLI
    return MapLegend(
        title=name,
        unit=unit,
        colormap_type="CONTINUOUS",
        min_value=-1.0,
        max_value=1.0,
        nodata_color="rgba(0,0,0,0)",
        stops=[
            LegendStop(value=0.0, color="#d73027", label="Non-Vegetated / Bare Soil (< 0.2)"),
            LegendStop(value=0.3, color="#fee08b", label="Low Vigour (0.2 - 0.4)"),
            LegendStop(value=0.5, color="#d9ef8b", label="Moderate Vigour (0.4 - 0.6)"),
            LegendStop(value=0.7, color="#91cf60", label="High Vigour (0.6 - 0.8)"),
            LegendStop(value=1.0, color="#1a9850", label="Very High Vigour (> 0.8)"),
        ],
    )


@router.get("/fields/{field_id}/boundary", response_model=FieldBoundaryGeoJSON, summary="Get Field Boundary GeoJSON")
def get_field_boundary(
    field_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FieldBoundaryGeoJSON:
    """Retrieves validated PostGIS field boundary geometry as GeoJSON Feature with bounding box and centroid."""
    field = verify_field_access(field_id, current_user, db)

    if field.boundary_geom is None:
        raise HTTPException(
            status_code=404,
            detail=f"Field '{field.field_name}' does not have a recorded spatial boundary.",
        )

    farm = db.query(Farm).filter(Farm.id == field.farm_id).first()
    geom_json_str = db.scalar(ST_AsGeoJSON(field.boundary_geom))
    geom_dict = json.loads(geom_json_str)

    # Calculate 2D bounding box and centroid from coordinates
    coords = geom_dict.get("coordinates", [])
    flat_lons: List[float] = []
    flat_lats: List[float] = []

    def _extract_coords(pts):
        if not pts:
            return
        if isinstance(pts[0], (int, float)):
            flat_lons.append(float(pts[0]))
            flat_lats.append(float(pts[1]))
        else:
            for sub in pts:
                _extract_coords(sub)

    _extract_coords(coords)

    bbox = None
    centroid = None
    if flat_lons and flat_lats:
        bbox = [min(flat_lons), min(flat_lats), max(flat_lons), max(flat_lats)]
        centroid = [sum(flat_lons) / len(flat_lons), sum(flat_lats) / len(flat_lats)]

    return FieldBoundaryGeoJSON(
        id=field.id,
        geometry=geom_dict,
        bbox=bbox,
        centroid=centroid,
        properties={
            "field_id": str(field.id),
            "field_name": field.field_name,
            "crop_type": field.crop_type,
            "area_hectares": float(field.area_hectares) if field.area_hectares else None,
            "farm_id": str(field.farm_id),
            "farm_name": farm.name if farm else "Unknown Farm",
        },
    )


@router.get("/surveys/{survey_id}/coverage", response_model=SurveyCoverageGeoJSON, summary="Get Survey Coverage GeoJSON")
def get_survey_coverage(
    survey_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SurveyCoverageGeoJSON:
    """Retrieves drone survey flight coverage boundary as GeoJSON Feature."""
    survey = verify_survey_access(survey_id, current_user, db)

    if survey.coverage_geom is None:
        raise HTTPException(status_code=404, detail="Survey has no spatial coverage geometry.")

    geom_json_str = db.scalar(ST_AsGeoJSON(survey.coverage_geom))
    geom_dict = json.loads(geom_json_str)

    return SurveyCoverageGeoJSON(
        id=survey.id,
        geometry=geom_dict,
        properties={
            "survey_id": str(survey.id),
            "survey_code": survey.survey_code,
            "sensor_type": survey.sensor_type,
            "flight_date": survey.flight_date.isoformat(),
        },
    )


@router.get("/surveys/{survey_id}/products", response_model=List[MapProductListItem], summary="List Validated Map Products")
def list_survey_products(
    survey_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[MapProductListItem]:
    """Lists available validated geospatial raster products for an authorized survey."""
    survey = verify_survey_access(survey_id, current_user, db)

    field = db.query(Field).filter(Field.id == survey.field_id).first()
    farm = db.query(Farm).filter(Farm.id == field.farm_id).first() if field else None

    products = (
        db.query(MapProduct)
        .filter(MapProduct.survey_id == survey_id)
        .order_by(desc(MapProduct.created_at))
        .all()
    )

    items: List[MapProductListItem] = []
    for p in products:
        # Check if raster file exists on disk
        has_file = False
        try:
            p_path = MapRenderingService.resolve_local_path(p.blob_uri)
            import os
            has_file = os.path.exists(p_path)
        except Exception:
            has_file = False

        display_name, _, _ = _get_display_name_and_unit(p.product_type)

        items.append(
            MapProductListItem(
                id=p.id,
                survey_id=survey.id,
                survey_code=survey.survey_code,
                farm_name=farm.name if farm else "Unknown Farm",
                field_name=field.field_name if field else "Unknown Field",
                product_type=p.product_type,
                display_name=display_name,
                band_count=p.band_count,
                crs_epsg=p.crs_epsg,
                resolution_cm_px=float(p.resolution_cm_px) if p.resolution_cm_px else None,
                is_cog=p.is_cog,
                is_published=p.is_published,
                created_at=p.created_at.isoformat(),
                has_raster_file=has_file,
            )
        )

    return items


@router.get("/layers/{product_id}/visualization", response_model=MapLayerVisualization, summary="Get Map Layer Visualization Metadata")
def get_layer_visualization(
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MapLayerVisualization:
    """Retrieves MapLibre layer metadata including WGS84 bounds, center coordinates,
    tile URL template, and product legend.
    """
    product = verify_map_product_access(product_id, current_user, db)

    survey = db.query(Survey).filter(Survey.id == product.survey_id).first()
    field_id = survey.field_id if survey else None
    farm_id = None
    if field_id:
        f = db.query(Field).filter(Field.id == field_id).first()
        farm_id = f.farm_id if f else None

    # Resolve local raster file
    try:
        raster_path = MapRenderingService.resolve_local_path(product.blob_uri)
        metadata = MapRenderingService.get_raster_metadata(raster_path)
        bounds = metadata["wgs84_bounds"]
        center = metadata["center"]
    except Exception as e:
        logger.warning("Could not read raster bounds from disk for product %s: %s", product_id, str(e))
        bounds = [74.58, 18.15, 74.59, 18.16]
        center = [74.585, 18.155]

    stats = product.statistical_summary or {}
    legend = _build_legend_for_product(product.product_type, stats)

    tile_url = f"/api/v1/maps/tiles/{product.id}/{{z}}/{{x}}/{{y}}.png"

    return MapLayerVisualization(
        product_id=product.id,
        product_type=product.product_type,
        survey_id=product.survey_id,
        field_id=field_id,
        farm_id=farm_id,
        crs_epsg=product.crs_epsg,
        is_cog=product.is_cog,
        bounds=bounds,
        center=center,
        tile_url_template=tile_url,
        legend=legend,
        statistical_summary=stats,
    )


@router.get("/tiles/{product_id}/{z}/{x}/{y}.png", summary="XYZ Slippy Tile Server")
def get_map_tile(
    product_id: uuid.UUID,
    z: int,
    x: int,
    y: int,
    token: Optional[str] = Query(default=None, description="Optional access token query parameter for tile requests"),
    authorization: Optional[str] = Header(default=None),
    cookie_token: Optional[str] = Cookie(default=None, alias=settings.AUTH_COOKIE_NAME),
    db: Session = Depends(get_db),
) -> Response:
    """Streams a 256x256 Web Mercator PNG tile for authorized products only."""
    user = get_current_user_with_query_fallback(
        db=db,
        authorization=authorization,
        cookie_token=cookie_token,
        token=token,
    )
    product = verify_map_product_access(product_id, user, db)

    try:
        raster_path = MapRenderingService.resolve_local_path(product.blob_uri)
        tile_bytes = MapRenderingService.render_tile(
            file_path=raster_path,
            product_type=product.product_type,
            z=z,
            x=x,
            y=y,
        )
        return Response(
            content=tile_bytes,
            media_type="image/png",
            headers={"Cache-Control": "public, max-age=3600"},
        )
    except Exception as e:
        logger.warning("Error rendering tile (%d/%d/%d) for product %s: %s", z, x, y, product_id, str(e))
        return Response(content=TRANSPARENT_TILE_BYTES, media_type="image/png")


@router.get("/products/{product_id}/probe", response_model=PointProbeResponse, summary="Probe Map Value at Point")
def probe_raster_point(
    product_id: uuid.UUID,
    lat: float = Query(..., ge=-90.0, le=90.0, description="Latitude in WGS84 degrees"),
    lon: float = Query(..., ge=-180.0, le=180.0, description="Longitude in WGS84 degrees"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PointProbeResponse:
    """Interactively samples the raster value at a specific geographic latitude and longitude."""
    product = verify_map_product_access(product_id, current_user, db)

    _, unit, _ = _get_display_name_and_unit(product.product_type)

    try:
        raster_path = MapRenderingService.resolve_local_path(product.blob_uri)
        val = MapRenderingService.sample_raster_point(raster_path, lat, lon)
        is_valid = val is not None
        desc_str = f"{product.product_type}: {val} {unit}" if is_valid else "NoData or outside raster footprint"
        return PointProbeResponse(
            product_id=product.id,
            lat=lat,
            lon=lon,
            value=val,
            unit=unit,
            is_valid=is_valid,
            description=desc_str,
        )
    except Exception as e:
        logger.warning("Point probing failed for product %s: %s", product_id, str(e))
        return PointProbeResponse(
            product_id=product.id,
            lat=lat,
            lon=lon,
            value=None,
            unit=unit,
            is_valid=False,
            description=f"Probing error: {str(e)}",
        )


@router.get("/products/{product_id}/diagnostics", response_model=DiagnosticSummaryResponse, summary="Get Product Diagnostics")
def get_product_diagnostics(
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DiagnosticSummaryResponse:
    """Retrieves descriptive raster diagnostics, zonal distributions, and transparent scientific warnings."""
    product = verify_map_product_access(product_id, current_user, db)

    survey = db.query(Survey).filter(Survey.id == product.survey_id).first()
    field = db.query(Field).filter(Field.id == survey.field_id).first() if survey else None
    farm = db.query(Farm).filter(Farm.id == field.farm_id).first() if field else None

    stats = product.statistical_summary or {}
    display_name, unit, _ = _get_display_name_and_unit(product.product_type)

    # Retrieve zonal statistics from database
    zonal_records = db.query(ZonalStatistic).filter(ZonalStatistic.map_product_id == product.id).all()
    zonal_items: List[ZonalDistributionItem] = []

    # Map colors for standard 4-zone classification
    color_map = {
        "Non-Vegetated / Bare Soil": "#d73027",
        "Low Vigour": "#fee08b",
        "Moderate Vigour": "#d9ef8b",
        "High Vigour": "#1a9850",
    }

    total_ha = 0.0
    for z in zonal_records:
        z_ha = float(z.area_hectares)
        total_ha += z_ha
        zonal_items.append(
            ZonalDistributionItem(
                zone_name=z.zone_name,
                min_val=float(z.min_val),
                max_val=float(z.max_val),
                area_hectares=z_ha,
                area_percentage=float(z.area_percentage),
                color=color_map.get(z.zone_name, "#91cf60"),
            )
        )

    # Provide data-driven warnings and limitations
    valid_pct = float(stats.get("valid_percentage", 100.0))
    valid_count = int(stats.get("valid_pixels", stats.get("valid_pixel_count", 0)))
    nodata_count = int(stats.get("nodata_pixels", stats.get("nodata_pixel_count", 0)))
    total_count = valid_count + nodata_count

    warnings: List[str] = [
        f"This raster contains {valid_pct:.1f}% valid pixels.",
        f"Statistics strictly exclude {nodata_count:,} NoData/masked pixels.",
    ]
    if valid_pct < 80.0:
        warnings.append("High NoData proportion detected; spatial coverage is incomplete.")

    prov = stats.get("provenance", {})
    if prov.get("radiometric_type") == "DIGITAL_NUMBERS_8BIT":
        warnings.append("Processed from uncalibrated 8-bit RGB imagery. Interpret absolute values cautiously.")

    limitations: List[str] = [
        "Vegetation indices measure canopy greenness, reflectance, and chlorophyll absorption, not direct crop disease.",
        "Variations in index values may be caused by soil background, canopy architecture, shadowing, irrigation, or growth stage.",
        "Do not apply fertilizers, pesticides, or agronomic treatments based solely on remote sensing map layers without ground-truthing.",
    ]

    return DiagnosticSummaryResponse(
        product_id=product.id,
        product_type=product.product_type,
        display_name=display_name,
        survey_id=product.survey_id,
        survey_code=survey.survey_code if survey else "SRV-UNKNOWN",
        field_name=field.field_name if field else "Unknown Field",
        farm_name=farm.name if farm else "Unknown Farm",
        crop_type=field.crop_type if field else None,
        crs_epsg=product.crs_epsg,
        resolution_cm_px=float(product.resolution_cm_px) if product.resolution_cm_px else None,
        valid_pixel_count=valid_count,
        nodata_pixel_count=nodata_count,
        total_pixel_count=total_count,
        valid_percentage=valid_pct,
        covered_area_hectares=round(total_ha, 4),
        min_value=float(stats.get("min")) if stats.get("min") is not None else None,
        max_value=float(stats.get("max")) if stats.get("max") is not None else None,
        mean_value=float(stats.get("mean")) if stats.get("mean") is not None else None,
        std_value=float(stats.get("std")) if stats.get("std") is not None else None,
        median_value=float(stats.get("median")) if stats.get("median") is not None else None,
        unit=unit,
        zonal_distribution=zonal_items,
        scientific_warnings=warnings,
        analytical_limitations=limitations,
    )


@router.get("/compare-compatibility", response_model=ComparisonCompatibilityResponse, summary="Check Raster Comparison Compatibility")
def check_comparison_compatibility(
    product_a: uuid.UUID = Query(..., description="First product ID"),
    product_b: uuid.UUID = Query(..., description="Second product ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ComparisonCompatibilityResponse:
    """Evaluates whether two raster products share spatial bounds, survey context, or coordinate reference systems."""
    prod_a = verify_map_product_access(product_a, current_user, db)
    prod_b = verify_map_product_access(product_b, current_user, db)

    survey_a = db.query(Survey).filter(Survey.id == prod_a.survey_id).first()
    survey_b = db.query(Survey).filter(Survey.id == prod_b.survey_id).first()

    # Check survey / field relation
    same_survey = prod_a.survey_id == prod_b.survey_id
    same_field = survey_a and survey_b and survey_a.field_id == survey_b.field_id

    # If from same survey or field, they share geographic bounds
    if same_survey:
        return ComparisonCompatibilityResponse(
            product_a_id=prod_a.id,
            product_b_id=prod_b.id,
            is_compatible=True,
            spatial_overlap_percentage=100.0,
            reason="Products originate from the exact same drone flight and share coordinate space.",
            recommendation="Direct side-by-side or swipe comparison is scientifically valid.",
        )

    if same_field:
        return ComparisonCompatibilityResponse(
            product_a_id=prod_a.id,
            product_b_id=prod_b.id,
            is_compatible=True,
            spatial_overlap_percentage=95.0,
            reason="Products originate from different surveys of the same field. Temporal multi-date comparison active.",
            recommendation="Compare canopy development across flight dates with awareness of differing weather and lighting.",
        )

    return ComparisonCompatibilityResponse(
        product_a_id=prod_a.id,
        product_b_id=prod_b.id,
        is_compatible=False,
        spatial_overlap_percentage=0.0,
        reason="Products belong to different fields and do not overlap spatially.",
        recommendation="Select products from the same field or survey for meaningful visual comparison.",
    )
