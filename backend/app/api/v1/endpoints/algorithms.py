import os
import logging
import uuid
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.api.deps import (
    get_db,
    get_current_user,
    verify_survey_access,
    verify_map_product_access,
    verify_algorithm_job_access,
)
from app.core.config import settings
from app.models.tenant import User, UserRole
from app.models.survey import Survey
from app.models.farm import Farm, Field
from app.models.file import SurveyFile
from app.models.product import Algorithm, AlgorithmJob, MapProduct, ZonalStatistic
from app.models.audit import AuditLog
from app.services.storage import get_storage_service
from app.services.raster_analytics import (
    RasterAnalyticsService,
    RasterInspection,
    BandSummary,
    RasterAnalyticsError,
)
from app.tasks.raster_analytics import trigger_algorithm_batch
from app.schemas.algorithms import (
    AlgorithmSpecResponse,
    BandSummarySchema,
    RasterInspectionResponse,
    EligibleRasterItem,
    EligibleRastersResponse,
    BandMappingValidateRequest,
    BandMappingValidateResponse,
    AlgorithmBatchCreateRequest,
    AlgorithmJobResponse,
    AlgorithmBatchResponse,
    ZonalStatItem,
    MapProductDetailResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/supported", response_model=List[AlgorithmSpecResponse], summary="List Supported Vegetation Index Algorithms")
def list_supported_algorithms(
    current_user: User = Depends(get_current_user),
) -> List[AlgorithmSpecResponse]:
    """Returns official definitions, formulas, required spectral bands, and parameter specs

    for all supported vegetation indices (NDVI, NDRE, GNDVI, SAVI, VARI, GLI).
    """
    specs = []
    for code, info in RasterAnalyticsService.ALGORITHM_SPECS.items():
        specs.append(
            AlgorithmSpecResponse(
                code=code,
                display_name=info["name"],
                required_sensor=info["sensor"],
                formula=info["formula"],
                required_bands=info["required_bands"],
                expected_range=info["expected_range"],
                description=info["description"],
                parameters=info.get("default_parameters"),
            )
        )
    return specs


@router.get("/eligible-rasters", response_model=EligibleRastersResponse, summary="List Eligible Source Rasters for Index Generation")
def list_eligible_rasters(
    survey_id: Optional[uuid.UUID] = Query(default=None, description="Filter by flight survey ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EligibleRastersResponse:
    """Lists eligible orthophotos (from WebODM photogrammetry) and pre-stitched GeoTIFF files

    available across surveys for vegetation index generation.
    """
    if survey_id:
        verify_survey_access(survey_id, current_user, db)

    items: List[EligibleRasterItem] = []

    # 1. Query MapProducts of type ORTHOPHOTO
    map_prod_query = (
        db.query(MapProduct, Survey, Farm, Field)
        .join(Survey, MapProduct.survey_id == Survey.id)
        .join(Field, Survey.field_id == Field.id)
        .join(Farm, Field.farm_id == Farm.id)
        .filter(MapProduct.product_type == "ORTHOPHOTO")
    )
    if current_user.role == UserRole.FARMER:
        map_prod_query = map_prod_query.filter(Farm.owner_id == current_user.id)
    if survey_id:
        map_prod_query = map_prod_query.filter(MapProduct.survey_id == survey_id)

    orthophotos = map_prod_query.order_by(desc(MapProduct.created_at)).all()

    for mp, s, farm, field in orthophotos:
        sensor = "MULTISPECTRAL" if mp.band_count >= 4 else "RGB"
        items.append(
            EligibleRasterItem(
                source_id=mp.id,
                source_type="MAP_PRODUCT",
                survey_id=s.id,
                survey_code=s.survey_code,
                farm_name=farm.name,
                field_name=field.field_name,
                filename=f"orthophoto_{s.survey_code}.tif",
                product_type=mp.product_type,
                band_count=mp.band_count,
                crs_epsg=mp.crs_epsg,
                resolution_cm_px=float(mp.resolution_cm_px) if mp.resolution_cm_px is not None else None,
                detected_sensor=sensor,
                is_eligible=True,
                ineligibility_reason=None,
                created_at=mp.created_at,
            )
        )

    # 2. Query SurveyFiles of type GEOTIFF
    survey_files_query = (
        db.query(SurveyFile, Survey, Farm, Field)
        .join(Survey, SurveyFile.survey_id == Survey.id)
        .join(Field, Survey.field_id == Field.id)
        .join(Farm, Field.farm_id == Farm.id)
        .filter(SurveyFile.file_type == "GEOTIFF")
    )
    if current_user.role == UserRole.FARMER:
        survey_files_query = survey_files_query.filter(Farm.owner_id == current_user.id)
    if survey_id:
        survey_files_query = survey_files_query.filter(SurveyFile.survey_id == survey_id)

    geotiffs = survey_files_query.order_by(desc(SurveyFile.created_at)).all()

    for sf, s, farm, field in geotiffs:
        is_val = sf.ingestion_status == "VALIDATED"
        items.append(
            EligibleRasterItem(
                source_id=sf.id,
                source_type="SURVEY_FILE",
                survey_id=s.id,
                survey_code=s.survey_code,
                farm_name=farm.name,
                field_name=field.field_name,
                filename=sf.original_filename,
                product_type="PRE_STITCHED_GEOTIFF",
                band_count=sf.band_count or 4,
                crs_epsg=sf.crs_epsg or "EPSG:4326",
                resolution_cm_px=float(sf.resolution_cm_px) if sf.resolution_cm_px is not None else None,
                detected_sensor=sf.sensor_type or ("MULTISPECTRAL" if (sf.band_count or 4) >= 4 else "RGB"),
                is_eligible=is_val,
                ineligibility_reason=None if is_val else f"Dataset status is {sf.ingestion_status}; must be VALIDATED.",
                created_at=sf.created_at,
            )
        )

    eligible_c = sum(1 for it in items if it.is_eligible)
    return EligibleRastersResponse(
        items=items,
        total=len(items),
        eligible_count=eligible_c,
        ineligible_count=len(items) - eligible_c,
    )


def _resolve_raster_file_path(
    db: Session,
    source_id: uuid.UUID,
    source_type: str,
    current_user: Optional[User] = None,
) -> Tuple[str, uuid.UUID, Survey, Farm, Field, MapProduct]:
    """Helper to resolve local filesystem path for a MapProduct or SurveyFile."""
    storage = get_storage_service()

    if source_type.upper() == "MAP_PRODUCT":
        mp = db.query(MapProduct).filter(MapProduct.id == source_id).first()
        if not mp:
            raise HTTPException(status_code=404, detail=f"MapProduct {source_id} not found.")

        survey = db.query(Survey).filter(Survey.id == mp.survey_id).first()
        field = db.query(Field).filter(Field.id == survey.field_id).first() if survey else None
        farm = db.query(Farm).filter(Farm.id == field.farm_id).first() if field else None

        if current_user and current_user.role == UserRole.FARMER:
            if not farm or farm.owner_id != current_user.id:
                raise HTTPException(status_code=404, detail=f"MapProduct {source_id} not found.")

        blob_uri = mp.blob_uri
        if blob_uri.startswith("local://"):
            parts = blob_uri.replace("local://", "").split("/", 1)
            file_path = storage._resolve_safe_path(parts[0], parts[1])
        else:
            raise HTTPException(
                status_code=400,
                detail="Direct raster inspection currently requires local accessible storage.",
            )

        return file_path, mp.survey_id, survey, farm, field, mp

    elif source_type.upper() == "SURVEY_FILE":
        sf = db.query(SurveyFile).filter(SurveyFile.id == source_id).first()
        if not sf:
            raise HTTPException(status_code=404, detail=f"SurveyFile {source_id} not found.")

        survey = db.query(Survey).filter(Survey.id == sf.survey_id).first()
        field = db.query(Field).filter(Field.id == survey.field_id).first() if survey else None
        farm = db.query(Farm).filter(Farm.id == field.farm_id).first() if field else None

        if current_user and current_user.role == UserRole.FARMER:
            if not farm or farm.owner_id != current_user.id:
                raise HTTPException(status_code=404, detail=f"SurveyFile {source_id} not found.")

        blob_uri = sf.blob_uri
        if blob_uri.startswith("local://"):
            parts = blob_uri.replace("local://", "").split("/", 1)
            file_path = storage._resolve_safe_path(parts[0], parts[1])
        else:
            raise HTTPException(
                status_code=400,
                detail="Direct raster inspection currently requires local accessible storage.",
            )

        # Ensure backing MapProduct exists
        existing_mp = db.query(MapProduct).filter(
            MapProduct.survey_id == sf.survey_id,
            MapProduct.blob_uri == sf.blob_uri,
        ).first()

        if not existing_mp:
            existing_mp = MapProduct(
                survey_id=sf.survey_id,
                product_type="ORTHOPHOTO",
                blob_uri=sf.blob_uri,
                is_cog=True,
                band_count=sf.band_count or 4,
                crs_epsg=sf.crs_epsg or "EPSG:4326",
                resolution_cm_px=sf.resolution_cm_px,
                is_published=False,
            )
            db.add(existing_mp)
            db.commit()
            db.refresh(existing_mp)

        return file_path, sf.survey_id, survey, farm, field, existing_mp

    else:
        raise HTTPException(status_code=400, detail=f"Invalid source_type: {source_type}")


@router.get("/inspect/{source_id}", response_model=RasterInspectionResponse, summary="Inspect Source Raster & Detect Spectral Channels")
def inspect_raster(
    source_id: uuid.UUID,
    source_type: str = Query(default="MAP_PRODUCT", description="'MAP_PRODUCT' or 'SURVEY_FILE'"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RasterInspectionResponse:
    """Inspects the geospatial and spectral properties of a raster file.

    Extracts band count, CRS, bounds, dynamic range, detected sensor type,
    suggested spectral channel mappings, and radiometric notes.
    """
    file_path, survey_id, survey, farm, field, _ = _resolve_raster_file_path(
        db, source_id, source_type, current_user=current_user
    )

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Underlying raster file not found on disk: {file_path}")

    try:
        inspection = RasterAnalyticsService.inspect_raster(file_path)
    except Exception as e:
        logger.exception("Raster inspection failed for %s: %s", source_id, str(e))
        raise HTTPException(status_code=422, detail=f"Raster inspection failed: {str(e)}")

    band_schemas = [
        BandSummarySchema(
            band_index=b.band_index,
            data_type=b.data_type,
            nodata_value=b.nodata_value,
            min_value=b.min_value,
            max_value=b.max_value,
            mean_value=b.mean_value,
            std_value=b.std_value,
            description=b.description,
        )
        for b in inspection.bands
    ]

    return RasterInspectionResponse(
        source_id=source_id,
        source_type=source_type.upper(),
        survey_id=survey_id,
        survey_code=survey.survey_code if survey else None,
        farm_name=farm.name if farm else None,
        field_name=field.field_name if field else None,
        width=inspection.width,
        height=inspection.height,
        band_count=inspection.band_count,
        crs_epsg=inspection.crs_epsg,
        bounds=inspection.bounds,
        gsd_cm=inspection.gsd_cm,
        detected_sensor=inspection.detected_sensor,
        radiometric_type=inspection.radiometric_type,
        calibration_notes=inspection.calibration_notes,
        suggested_band_mapping=inspection.suggested_band_mapping,
        supported_algorithms=inspection.supported_algorithms,
        bands=band_schemas,
    )


@router.post("/validate-mapping", response_model=BandMappingValidateResponse, summary="Validate Spectral Band Mapping")
def validate_band_mapping(
    req: BandMappingValidateRequest,
    current_user: User = Depends(get_current_user),
) -> BandMappingValidateResponse:
    """Validates whether a user-defined spectral channel mapping meets the mathematical

    requirements for one or more requested algorithms.
    """
    per_algo = {}
    all_valid = True
    messages = []

    for code in req.algorithm_codes:
        is_v, err = RasterAnalyticsService.validate_band_mapping(
            band_count=req.band_count,
            mapping=req.mapping,
            algorithm_code=code,
        )
        per_algo[code] = {
            "is_valid": is_v,
            "error_message": err,
        }
        if not is_v:
            all_valid = False
            messages.append(f"{code}: {err}")

    overall = "All requested algorithms are compatible." if all_valid else "; ".join(messages)
    return BandMappingValidateResponse(
        is_valid=all_valid,
        per_algorithm_status=per_algo,
        overall_message=overall,
    )


@router.post(
    "/jobs",
    response_model=AlgorithmBatchResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit Multi-Map Vegetation Index Batch Job",
)
def submit_algorithm_batch(
    payload: AlgorithmBatchCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AlgorithmBatchResponse:
    """Creates a batch of asynchronous vegetation index processing jobs (NDVI, NDRE, GNDVI, SAVI, VARI, GLI)

    for an eligible source raster and dispatches execution to background workers.
    """
    file_path, survey_id, survey, farm, field, map_product = _resolve_raster_file_path(
        db, payload.source_id, payload.source_type, current_user=current_user
    )

    batch_id = uuid.uuid4()
    jobs_created: List[AlgorithmJob] = []

    for algo_req in payload.algorithms:
        algo_code = algo_req.algorithm_code.upper()

        # Pre-validate band mapping
        is_v, err = RasterAnalyticsService.validate_band_mapping(
            band_count=map_product.band_count,
            mapping=payload.band_mapping,
            algorithm_code=algo_code,
        )
        if not is_v:
            raise HTTPException(
                status_code=400,
                detail=f"Incompatible band mapping for {algo_code}: {err}",
            )

        job_params = {
            "band_mapping": payload.band_mapping,
            **(algo_req.parameters or {}),
        }

        job = AlgorithmJob(
            batch_id=batch_id,
            input_product_id=map_product.id,
            algorithm_code=algo_code,
            parameters=job_params,
            status="QUEUED",
            current_stage="QUEUED",
            progress_percent=0,
            error_message=None,
            retry_count=0,
            started_at=datetime.utcnow(),
        )
        db.add(job)
        jobs_created.append(job)

    db.commit()

    # Refresh jobs to get IDs
    for j in jobs_created:
        db.refresh(j)

    # Record Audit Log
    try:
        audit = AuditLog(
            user_id=current_user.id,
            action="DISPATCH_ALGORITHM_BATCH",
            entity_type="algorithm_jobs",
            entity_id=batch_id,
        )
        db.add(audit)
        db.commit()
    except Exception as e:
        logger.warning("Audit log recording failed: %s", str(e))

    # Dispatch to background worker
    trigger_algorithm_batch(batch_id)

    job_responses = [
        AlgorithmJobResponse(
            job_id=j.id,
            batch_id=j.batch_id,
            algorithm_code=j.algorithm_code,
            algorithm_name=RasterAnalyticsService.ALGORITHM_SPECS.get(j.algorithm_code, {}).get("name", j.algorithm_code),
            input_product_id=j.input_product_id,
            status=j.status,
            current_stage=j.current_stage,
            progress_percent=j.progress_percent,
            error_message=j.error_message,
            parameters=j.parameters,
            output_product_id=j.output_product_id,
            started_at=j.started_at,
            completed_at=j.completed_at,
        )
        for j in jobs_created
    ]

    return AlgorithmBatchResponse(
        batch_id=batch_id,
        survey_id=survey_id,
        input_product_id=map_product.id,
        total_jobs=len(jobs_created),
        completed_jobs=0,
        failed_jobs=0,
        in_progress_jobs=len(jobs_created),
        status="QUEUED",
        jobs=job_responses,
    )


@router.get("/batches/{batch_id}", response_model=AlgorithmBatchResponse, summary="Get Multi-Map Batch Status")
def get_batch_status(
    batch_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AlgorithmBatchResponse:
    """Retrieves live status, progress, and generated products for all jobs in an algorithm batch."""
    jobs = (
        db.query(AlgorithmJob)
        .filter(AlgorithmJob.batch_id == batch_id)
        .order_by(AlgorithmJob.started_at.asc())
        .all()
    )

    if not jobs:
        raise HTTPException(status_code=404, detail=f"Algorithm batch {batch_id} not found.")

    first_job = jobs[0]
    verify_algorithm_job_access(first_job.id, current_user, db)

    input_product = db.query(MapProduct).filter(MapProduct.id == first_job.input_product_id).first()
    survey_id = input_product.survey_id if input_product else uuid.uuid4()

    completed_c = sum(1 for j in jobs if j.status == "COMPLETED")
    failed_c = sum(1 for j in jobs if j.status == "FAILED")
    in_prog_c = sum(1 for j in jobs if j.status in ("QUEUED", "PREPARING", "RUNNING", "VALIDATING", "STORING"))

    if completed_c == len(jobs):
        batch_status = "COMPLETED"
    elif failed_c == len(jobs):
        batch_status = "FAILED"
    elif completed_c > 0 and (completed_c + failed_c) == len(jobs):
        batch_status = "PARTIALLY_COMPLETED"
    elif in_prog_c > 0:
        batch_status = "RUNNING"
    else:
        batch_status = "QUEUED"

    job_responses = [
        AlgorithmJobResponse(
            job_id=j.id,
            batch_id=j.batch_id,
            algorithm_code=j.algorithm_code,
            algorithm_name=RasterAnalyticsService.ALGORITHM_SPECS.get(j.algorithm_code, {}).get("name", j.algorithm_code),
            input_product_id=j.input_product_id,
            status=j.status,
            current_stage=j.current_stage,
            progress_percent=j.progress_percent,
            error_message=j.error_message,
            parameters=j.parameters,
            output_product_id=j.output_product_id,
            started_at=j.started_at,
            completed_at=j.completed_at,
        )
        for j in jobs
    ]

    return AlgorithmBatchResponse(
        batch_id=batch_id,
        survey_id=survey_id,
        input_product_id=first_job.input_product_id,
        total_jobs=len(jobs),
        completed_jobs=completed_c,
        failed_jobs=failed_c,
        in_progress_jobs=in_prog_c,
        status=batch_status,
        jobs=job_responses,
    )


@router.get("/jobs", response_model=List[AlgorithmJobResponse], summary="List Algorithm Processing Jobs")
def list_algorithm_jobs(
    survey_id: Optional[uuid.UUID] = Query(default=None, description="Filter jobs by survey ID"),
    status: Optional[str] = Query(default=None, description="Filter by status: QUEUED | RUNNING | COMPLETED | FAILED"),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[AlgorithmJobResponse]:
    """Lists recent algorithm execution jobs with live status, progress percentage, and output references."""
    query = (
        db.query(AlgorithmJob)
        .join(MapProduct, AlgorithmJob.input_product_id == MapProduct.id)
        .join(Survey, MapProduct.survey_id == Survey.id)
        .join(Field, Survey.field_id == Field.id)
        .join(Farm, Field.farm_id == Farm.id)
    )

    if current_user.role == UserRole.FARMER:
        query = query.filter(Farm.owner_id == current_user.id)

    if survey_id:
        verify_survey_access(survey_id, current_user, db)
        query = query.filter(MapProduct.survey_id == survey_id)
    if status:
        query = query.filter(AlgorithmJob.status == status.upper())

    jobs = query.order_by(desc(AlgorithmJob.started_at)).limit(limit).all()

    return [
        AlgorithmJobResponse(
            job_id=j.id,
            batch_id=j.batch_id,
            algorithm_code=j.algorithm_code,
            algorithm_name=RasterAnalyticsService.ALGORITHM_SPECS.get(j.algorithm_code, {}).get("name", j.algorithm_code),
            input_product_id=j.input_product_id,
            status=j.status,
            current_stage=j.current_stage,
            progress_percent=j.progress_percent,
            error_message=j.error_message,
            parameters=j.parameters,
            output_product_id=j.output_product_id,
            started_at=j.started_at,
            completed_at=j.completed_at,
        )
        for j in jobs
    ]


@router.get("/jobs/{job_id}", response_model=AlgorithmJobResponse, summary="Get Single Algorithm Job")
def get_algorithm_job(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AlgorithmJobResponse:
    """Retrieves full details and output references for a specific algorithm processing job."""
    job = verify_algorithm_job_access(job_id, current_user, db)

    return AlgorithmJobResponse(
        job_id=job.id,
        batch_id=job.batch_id,
        algorithm_code=job.algorithm_code,
        algorithm_name=RasterAnalyticsService.ALGORITHM_SPECS.get(job.algorithm_code, {}).get("name", job.algorithm_code),
        input_product_id=job.input_product_id,
        status=job.status,
        current_stage=job.current_stage,
        progress_percent=job.progress_percent,
        error_message=job.error_message,
        parameters=job.parameters,
        output_product_id=job.output_product_id,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )


@router.post("/jobs/{job_id}/retry", response_model=AlgorithmJobResponse, summary="Retry Failed Algorithm Job")
def retry_algorithm_job(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AlgorithmJobResponse:
    """Retries a failed algorithm job by resetting status and redispatching execution."""
    job = verify_algorithm_job_access(job_id, current_user, db)

    if job.status not in ("FAILED", "CANCELLED"):
        raise HTTPException(
            status_code=400,
            detail=f"Only FAILED or CANCELLED jobs can be retried. Current status is {job.status}.",
        )

    # Assign new batch_id if none exists
    new_batch_id = job.batch_id or uuid.uuid4()
    job.batch_id = new_batch_id
    job.status = "QUEUED"
    job.current_stage = "QUEUED"
    job.progress_percent = 0
    job.error_message = None
    job.retry_count = (job.retry_count or 0) + 1
    job.started_at = datetime.utcnow()
    job.completed_at = None
    db.commit()
    db.refresh(job)

    # Dispatch to background
    trigger_algorithm_batch(new_batch_id)

    return AlgorithmJobResponse(
        job_id=job.id,
        batch_id=job.batch_id,
        algorithm_code=job.algorithm_code,
        algorithm_name=RasterAnalyticsService.ALGORITHM_SPECS.get(job.algorithm_code, {}).get("name", job.algorithm_code),
        input_product_id=job.input_product_id,
        status=job.status,
        current_stage=job.current_stage,
        progress_percent=job.progress_percent,
        error_message=job.error_message,
        parameters=job.parameters,
        output_product_id=job.output_product_id,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )


@router.get("/products/{product_id}", response_model=MapProductDetailResponse, summary="Get Map Product Details & Zonal Statistics")
def get_map_product_detail(
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MapProductDetailResponse:
    """Retrieves metadata, statistical summary, secure download URI,

    and agronomic zonal classifications for a generated index MapProduct.
    """
    product = verify_map_product_access(product_id, current_user, db)

    storage = get_storage_service()
    container = settings.AZURE_CONTAINER_INDICES
    blob_path = product.blob_uri.replace(f"local://{container}/", "").replace(f"azure://{container}/", "")
    access_url = storage.get_access_url(container, blob_path)

    # Fetch zonal statistics
    zonal_records = (
        db.query(ZonalStatistic)
        .filter(ZonalStatistic.map_product_id == product.id)
        .order_by(ZonalStatistic.min_val.asc())
        .all()
    )

    zonal_items = [
        ZonalStatItem(
            zone_name=z.zone_name,
            min_val=float(z.min_val),
            max_val=float(z.max_val),
            area_hectares=float(z.area_hectares),
            area_percentage=float(z.area_percentage),
        )
        for z in zonal_records
    ]

    return MapProductDetailResponse(
        product_id=product.id,
        survey_id=product.survey_id,
        source_job_id=product.source_job_id,
        product_type=product.product_type,
        blob_uri=product.blob_uri,
        access_url=access_url,
        is_cog=product.is_cog,
        band_count=product.band_count,
        crs_epsg=product.crs_epsg,
        resolution_cm_px=float(product.resolution_cm_px) if product.resolution_cm_px is not None else None,
        statistical_summary=product.statistical_summary,
        zonal_statistics=zonal_items,
        created_at=product.created_at,
    )
