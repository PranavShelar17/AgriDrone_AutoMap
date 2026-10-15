import logging
from uuid import UUID
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.api.deps import (
    get_db,
    get_current_user,
    verify_survey_access,
    verify_task_access,
)
from app.core.config import settings
from app.models.tenant import User, UserRole
from app.models.survey import Survey
from app.models.file import SurveyFile
from app.models.farm import Farm, Field
from app.models.task import PhotogrammetryTask, TaskLog
from app.models.product import MapProduct
from app.models.audit import AuditLog
from app.services.webodm import get_webodm_service
from app.services.storage import get_storage_service
from app.tasks.photogrammetry import trigger_photogrammetry_task, append_task_log
from app.schemas.photogrammetry import (
    EligibleDatasetItem,
    EligibleDatasetsResponse,
    PhotogrammetryTaskCreate,
    PhotogrammetryTaskResponse,
    PhotogrammetryTaskListResponse,
    TaskLogItem,
    TaskLogsResponse,
    ClusterStatusResponse,
    ArtifactItem,
    ArtifactListResponse,
    TaskActionResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/cluster-status", response_model=ClusterStatusResponse, summary="Probe WebODM/NodeODM Cluster Health")
def get_cluster_status(
    current_user: User = Depends(get_current_user),
) -> ClusterStatusResponse:
    """Probes the configured WebODM or NodeODM service and returns live connection and capacity metrics."""
    webodm = get_webodm_service()
    health_data = webodm.check_cluster_health()
    return ClusterStatusResponse(**health_data)


@router.get("/eligible-datasets", response_model=EligibleDatasetsResponse, summary="List Eligible Datasets for Photogrammetry")
def list_eligible_datasets(
    survey_id: Optional[UUID] = Query(default=None, description="Filter datasets by specific flight survey"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EligibleDatasetsResponse:
    """
    Returns survey datasets with photogrammetry eligibility status and explicit rejection rationales.
    Only validated raw aerial photographs (JPEG/TIFF or archives) are eligible for WebODM photogrammetry.
    Pre-stitched GeoTIFF rasters are flagged as ineligible for photogrammetry (they bypass to Phase 7 GIS).
    """
    query = (
        db.query(SurveyFile, Survey, Field, Farm)
        .join(Survey, SurveyFile.survey_id == Survey.id)
        .join(Field, Survey.field_id == Field.id)
        .join(Farm, Field.farm_id == Farm.id)
    )

    if current_user.role == UserRole.FARMER:
        query = query.filter(Farm.owner_id == current_user.id)

    if survey_id:
        query = query.filter(SurveyFile.survey_id == survey_id)

    records = query.order_by(desc(SurveyFile.created_at)).all()
    storage = get_storage_service()

    items: List[EligibleDatasetItem] = []
    eligible_count = 0
    ineligible_count = 0

    # Active tasks lookup to detect conflicts
    active_survey_tasks = {
        task.survey_id
        for task in db.query(PhotogrammetryTask.survey_id)
        .filter(PhotogrammetryTask.status.in_(["SUBMITTED", "QUEUED", "PREPARING", "UPLOADING", "RUNNING", "FINALIZING"]))
        .all()
    }

    for sfile, survey, field, farm in records:
        meta = sfile.validation_metadata or {}
        val_errors = meta.get("validation_errors", [])
        workflow = meta.get("workflow_route", "NONE")
        sub_meta = meta.get("metadata", {})

        is_eligible = True
        ineligibility_reason = None

        # 1. Ingestion status check
        if sfile.ingestion_status == "REJECTED":
            is_eligible = False
            reasons = "; ".join(val_errors) if val_errors else "File failed ingestion validation"
            ineligibility_reason = f"Rejected: {reasons}"

        # 2. GeoTIFF pre-stitched check (Distinguish raw vs GeoTIFF)
        elif sfile.file_type == "GEOTIFF" or workflow == "DIRECT_ALGORITHM_GIS":
            is_eligible = False
            ineligibility_reason = "Pre-stitched GeoTIFF rasters bypass WebODM photogrammetry and route directly to Phase 7 GIS algorithms."

        # 3. Unsupported file type check
        elif sfile.file_type not in ("RAW_IMAGE", "RAW_ZIP"):
            is_eligible = False
            ineligibility_reason = f"Unsupported file type for photogrammetry: {sfile.file_type}"

        # 4. Storage accessibility check
        else:
            blob_path = sfile.blob_uri.split(f"{settings.AZURE_CONTAINER_RAW}/")[-1]
            if blob_path.startswith("local://"):
                blob_path = blob_path.replace(f"local://{settings.AZURE_CONTAINER_RAW}/", "")

            try:
                if not storage.file_exists(settings.AZURE_CONTAINER_RAW, blob_path):
                    is_eligible = False
                    ineligibility_reason = "Dataset file is not accessible on the storage backend."
            except Exception:
                is_eligible = False
                ineligibility_reason = "Storage backend verification failed for this file."

        # 5. Check if survey has active processing conflict
        if is_eligible and survey.id in active_survey_tasks:
            is_eligible = False
            ineligibility_reason = "Survey currently has an active photogrammetry reconstruction job running."

        if is_eligible:
            eligible_count += 1
        else:
            ineligible_count += 1

        photo_count = sub_meta.get("extracted_image_count") if sfile.file_type == "RAW_ZIP" else 1

        items.append(
            EligibleDatasetItem(
                file_id=sfile.id,
                survey_id=sfile.survey_id,
                survey_code=survey.survey_code,
                farm_name=farm.name,
                field_name=field.field_name,
                original_filename=sfile.original_filename,
                file_type=sfile.file_type,
                file_size_bytes=sfile.file_size_bytes,
                ingestion_status=sfile.ingestion_status,
                workflow_route=workflow,
                is_eligible=is_eligible,
                ineligibility_reason=ineligibility_reason,
                photo_count_estimate=photo_count,
                camera_model=sub_meta.get("camera_model"),
                created_at=sfile.created_at,
            )
        )

    return EligibleDatasetsResponse(
        items=items,
        total=len(items),
        eligible_count=eligible_count,
        ineligible_count=ineligible_count,
    )


@router.post("/tasks", response_model=PhotogrammetryTaskResponse, status_code=status.HTTP_202_ACCEPTED, summary="Dispatch Photogrammetry Reconstruction Task")
def create_photogrammetry_task(
    payload: PhotogrammetryTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PhotogrammetryTaskResponse:
    """
    Validates dataset eligibility, checks concurrency, creates a photogrammetry_tasks record,
    and dispatches asynchronous photogrammetry reconstruction.
    """
    # 1. Survey existence & authorization check
    survey = verify_survey_access(payload.survey_id, current_user, db)

    # 2. Source file validation if specified
    source_file: Optional[SurveyFile] = None
    if payload.source_file_id:
        source_file = (
            db.query(SurveyFile)
            .filter(SurveyFile.id == payload.source_file_id, SurveyFile.survey_id == payload.survey_id)
            .first()
        )
        if not source_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Source dataset '{payload.source_file_id}' does not belong to survey '{payload.survey_id}'.",
            )

        if source_file.ingestion_status != "VALIDATED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Dataset '{source_file.original_filename}' cannot be processed because ingestion status is {source_file.ingestion_status}.",
            )

        if source_file.file_type == "GEOTIFF":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pre-stitched GeoTIFF rasters cannot be submitted for WebODM photogrammetry. Use Phase 7 Direct GIS processing.",
            )
    else:
        # Check if survey has any validated raw photo files
        valid_files_count = (
            db.query(SurveyFile)
            .filter(
                SurveyFile.survey_id == payload.survey_id,
                SurveyFile.ingestion_status == "VALIDATED",
                SurveyFile.file_type.in_(["RAW_IMAGE", "RAW_ZIP"]),
            )
            .count()
        )
        if valid_files_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Survey '{survey.survey_code}' has no validated raw drone photographs to process.",
            )

    # 3. Concurrency / Duplicate check
    active_task = (
        db.query(PhotogrammetryTask)
        .filter(
            PhotogrammetryTask.survey_id == payload.survey_id,
            PhotogrammetryTask.status.in_(["SUBMITTED", "QUEUED", "PREPARING", "UPLOADING", "RUNNING", "FINALIZING"]),
        )
        .first()
    )
    if active_task:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A photogrammetry task (ID: {active_task.id}) is already active ({active_task.status}) for survey '{survey.survey_code}'. Wait for completion or cancel it before starting another run.",
        )

    # 4. Construct task options JSONB
    task_options = {
        "resolution_preset": payload.resolution_preset,
        "custom_resolution_cm": payload.custom_resolution_cm,
        "generate_dsm": payload.generate_dsm,
        "generate_dtm": payload.generate_dtm,
        "radiometric_calibration": payload.radiometric_calibration,
        "feature_quality": payload.feature_quality,
        "pc_quality": payload.pc_quality,
    }

    # 5. Insert Task record
    new_task = PhotogrammetryTask(
        survey_id=payload.survey_id,
        source_file_id=payload.source_file_id,
        resolution_preset=payload.resolution_preset,
        generate_dsm=payload.generate_dsm,
        generate_dtm=payload.generate_dtm,
        radiometric_calibration=payload.radiometric_calibration,
        options=task_options,
        status="SUBMITTED",
        progress_percent=0,
        current_stage="Job submitted to queue",
        started_at=datetime.utcnow(),
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    # 6. Initial task log
    append_task_log(db, new_task.id, f"Photogrammetry job submitted by administrator {current_user.email}")
    append_task_log(db, new_task.id, f"Preset: {payload.resolution_preset} | DSM: {payload.generate_dsm} | DTM: {payload.generate_dtm}")

    # 7. Audit log
    audit_entry = AuditLog(
        user_id=current_user.id,
        action="DISPATCH_PHOTOGRAMMETRY",
        entity_type="photogrammetry_tasks",
        entity_id=new_task.id,
    )
    db.add(audit_entry)
    db.commit()

    # 8. Dispatch asynchronous background execution
    trigger_photogrammetry_task(new_task.id)

    return PhotogrammetryTaskResponse(
        task_id=new_task.id,
        survey_id=new_task.survey_id,
        survey_code=survey.survey_code,
        source_file_id=new_task.source_file_id,
        source_filename=source_file.original_filename if source_file else None,
        webodm_task_uuid=new_task.webodm_task_uuid,
        resolution_preset=new_task.resolution_preset,
        generate_dsm=new_task.generate_dsm,
        generate_dtm=new_task.generate_dtm,
        radiometric_calibration=new_task.radiometric_calibration,
        options=new_task.options,
        status=new_task.status,
        progress_percent=new_task.progress_percent,
        current_stage=new_task.current_stage,
        error_message=new_task.error_message,
        retry_count=new_task.retry_count,
        started_at=new_task.started_at,
        completed_at=new_task.completed_at,
        generated_products_count=0,
    )


@router.get("/tasks", response_model=PhotogrammetryTaskListResponse, summary="List Photogrammetry Tasks")
def list_photogrammetry_tasks(
    survey_id: Optional[UUID] = Query(default=None, description="Filter by flight survey"),
    status: Optional[str] = Query(default=None, description="Filter by task status"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PhotogrammetryTaskListResponse:
    """Lists photogrammetry tasks with pagination, filters, and deliverable counts."""
    query = db.query(PhotogrammetryTask, Survey).join(Survey, PhotogrammetryTask.survey_id == Survey.id)

    if current_user.role == UserRole.FARMER:
        query = query.join(Field, Survey.field_id == Field.id).join(Farm, Field.farm_id == Farm.id).filter(Farm.owner_id == current_user.id)

    if survey_id:
        query = query.filter(PhotogrammetryTask.survey_id == survey_id)
    if status:
        query = query.filter(PhotogrammetryTask.status == status.upper())

    total = query.count()
    records = query.order_by(desc(PhotogrammetryTask.started_at)).offset(skip).limit(limit).all()

    items: List[PhotogrammetryTaskResponse] = []
    for task, survey in records:
        source_filename = None
        if task.source_file_id:
            sfile = db.query(SurveyFile).filter(SurveyFile.id == task.source_file_id).first()
            if sfile:
                source_filename = sfile.original_filename

        prod_count = db.query(MapProduct).filter(MapProduct.source_task_id == task.id).count()

        items.append(
            PhotogrammetryTaskResponse(
                task_id=task.id,
                survey_id=task.survey_id,
                survey_code=survey.survey_code,
                source_file_id=task.source_file_id,
                source_filename=source_filename,
                webodm_task_uuid=task.webodm_task_uuid,
                resolution_preset=task.resolution_preset,
                generate_dsm=task.generate_dsm,
                generate_dtm=task.generate_dtm,
                radiometric_calibration=task.radiometric_calibration,
                options=task.options,
                status=task.status,
                progress_percent=task.progress_percent,
                current_stage=task.current_stage,
                error_message=task.error_message,
                retry_count=task.retry_count,
                started_at=task.started_at,
                completed_at=task.completed_at,
                generated_products_count=prod_count,
            )
        )

    return PhotogrammetryTaskListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/tasks/{task_id}", response_model=PhotogrammetryTaskResponse, summary="Get Photogrammetry Task Details")
def get_photogrammetry_task(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PhotogrammetryTaskResponse:
    """Retrieves detailed status, progress, and stage metrics for a specific photogrammetry task."""
    task = verify_task_access(task_id, current_user, db)

    survey = db.query(Survey).filter(Survey.id == task.survey_id).first()
    source_filename = None
    if task.source_file_id:
        sfile = db.query(SurveyFile).filter(SurveyFile.id == task.source_file_id).first()
        if sfile:
            source_filename = sfile.original_filename

    prod_count = db.query(MapProduct).filter(MapProduct.source_task_id == task.id).count()

    return PhotogrammetryTaskResponse(
        task_id=task.id,
        survey_id=task.survey_id,
        survey_code=survey.survey_code if survey else None,
        source_file_id=task.source_file_id,
        source_filename=source_filename,
        webodm_task_uuid=task.webodm_task_uuid,
        resolution_preset=task.resolution_preset,
        generate_dsm=task.generate_dsm,
        generate_dtm=task.generate_dtm,
        radiometric_calibration=task.radiometric_calibration,
        options=task.options,
        status=task.status,
        progress_percent=task.progress_percent,
        current_stage=task.current_stage,
        error_message=task.error_message,
        retry_count=task.retry_count,
        started_at=task.started_at,
        completed_at=task.completed_at,
        generated_products_count=prod_count,
    )


@router.get("/tasks/{task_id}/logs", response_model=TaskLogsResponse, summary="Get Task Console Logs")
def get_task_logs(
    task_id: UUID,
    limit: int = Query(default=500, ge=1, le=2000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskLogsResponse:
    """Retrieves real-time console execution logs stored for the task."""
    task = verify_task_access(task_id, current_user, db)

    logs = (
        db.query(TaskLog)
        .filter(TaskLog.task_id == task_id)
        .order_by(TaskLog.id.asc())
        .limit(limit)
        .all()
    )

    items = [
        TaskLogItem(
            id=log.id,
            task_id=log.task_id,
            log_level=log.log_level,
            message=log.message,
            logged_at=log.logged_at,
        )
        for log in logs
    ]

    return TaskLogsResponse(
        task_id=task_id,
        logs=items,
        total_lines=len(items),
    )


@router.get("/tasks/{task_id}/artifacts", response_model=ArtifactListResponse, summary="List Generated Output Deliverables")
def get_task_artifacts(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ArtifactListResponse:
    """Lists registered MapProduct outputs (orthophoto, DSM, DTM) generated by this photogrammetry run."""
    task = verify_task_access(task_id, current_user, db)

    products = (
        db.query(MapProduct)
        .filter(MapProduct.source_task_id == task_id)
        .order_by(MapProduct.created_at.asc())
        .all()
    )

    items = [
        ArtifactItem(
            product_id=p.id,
            survey_id=p.survey_id,
            source_task_id=p.source_task_id,
            product_type=p.product_type,
            original_filename=f"{p.product_type.lower()}_{str(p.id)[:8]}.tif",
            blob_uri=p.blob_uri,
            is_cog=p.is_cog,
            band_count=p.band_count,
            crs_epsg=p.crs_epsg,
            resolution_cm_px=float(p.resolution_cm_px) if p.resolution_cm_px else None,
            created_at=p.created_at,
        )
        for p in products
    ]

    return ArtifactListResponse(
        task_id=task_id,
        survey_id=task.survey_id,
        items=items,
        total=len(items),
    )


@router.post("/tasks/{task_id}/cancel", response_model=TaskActionResponse, summary="Cancel Running Photogrammetry Task")
def cancel_photogrammetry_task(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskActionResponse:
    """Cancels an active or queued photogrammetry task."""
    task = verify_task_access(task_id, current_user, db)

    if task.status in ("COMPLETED", "FAILED", "CANCELLED"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel task in terminal state '{task.status}'.",
        )

    task.status = "CANCEL_REQUESTED"
    db.commit()
    append_task_log(db, task.id, f"Cancellation requested by {current_user.email}", "WARNING")

    # If webodm_task_uuid exists, invoke cancel on WebODM directly
    webodm = get_webodm_service()
    if task.webodm_task_uuid:
        try:
            webodm.cancel_task(task.webodm_task_uuid)
            task.status = "CANCELLED"
            task.completed_at = datetime.utcnow()
            task.current_stage = "Cancelled by user"
            db.commit()
            append_task_log(db, task.id, "WebODM task successfully cancelled.", "WARNING")
        except Exception as e:
            logger.warning("Error issuing cancel to WebODM: %s", str(e))
    else:
        task.status = "CANCELLED"
        task.completed_at = datetime.utcnow()
        task.current_stage = "Cancelled before dispatch"
        db.commit()

    # Reset survey status
    survey = db.query(Survey).filter(Survey.id == task.survey_id).first()
    if survey and survey.status == "PROCESSING":
        survey.status = "DRAFT"
        db.commit()

    return TaskActionResponse(
        task_id=task.id,
        status=task.status,
        message="Task cancellation processed successfully.",
    )


@router.post("/tasks/{task_id}/retry", response_model=PhotogrammetryTaskResponse, status_code=status.HTTP_202_ACCEPTED, summary="Retry Failed or Cancelled Task")
def retry_photogrammetry_task(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PhotogrammetryTaskResponse:
    """Re-dispatches a failed or cancelled photogrammetry task with fresh execution."""
    task = verify_task_access(task_id, current_user, db)

    if task.status not in ("FAILED", "CANCELLED"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot retry task in state '{task.status}'. Only FAILED or CANCELLED tasks can be retried.",
        )

    task.retry_count += 1
    task.status = "SUBMITTED"
    task.progress_percent = 0
    task.current_stage = f"Retry #{task.retry_count} queued"
    task.error_message = None
    task.started_at = datetime.utcnow()
    task.completed_at = None
    db.commit()

    append_task_log(db, task.id, f"Retry attempt #{task.retry_count} initiated by {current_user.email}")

    # Dispatch execution
    trigger_photogrammetry_task(task.id)

    survey = db.query(Survey).filter(Survey.id == task.survey_id).first()
    source_filename = None
    if task.source_file_id:
        sfile = db.query(SurveyFile).filter(SurveyFile.id == task.source_file_id).first()
        if sfile:
            source_filename = sfile.original_filename

    return PhotogrammetryTaskResponse(
        task_id=task.id,
        survey_id=task.survey_id,
        survey_code=survey.survey_code if survey else None,
        source_file_id=task.source_file_id,
        source_filename=source_filename,
        webodm_task_uuid=task.webodm_task_uuid,
        resolution_preset=task.resolution_preset,
        generate_dsm=task.generate_dsm,
        generate_dtm=task.generate_dtm,
        radiometric_calibration=task.radiometric_calibration,
        options=task.options,
        status=task.status,
        progress_percent=task.progress_percent,
        current_stage=task.current_stage,
        error_message=task.error_message,
        retry_count=task.retry_count,
        started_at=task.started_at,
        completed_at=task.completed_at,
        generated_products_count=0,
    )
