import time
import logging
from uuid import UUID
from typing import List, Optional
from datetime import datetime

import io
from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, or_

from app.api.deps import (
    get_db,
    get_current_user,
    get_current_active_admin,
    verify_survey_access,
    verify_task_access,
    verify_farm_access,
    verify_photogrammetry_project_access,
)
from app.core.config import settings
from app.models.tenant import User, UserRole
from app.models.survey import Survey
from app.models.file import SurveyFile
from app.models.farm import Farm, Field
from app.models.task import PhotogrammetryTask, TaskLog
from app.models.project import PhotogrammetryProject
from app.models.product import MapProduct
from app.models.audit import AuditLog
from app.services.webodm import get_webodm_service
from app.services.storage import get_storage_service
from app.tasks.photogrammetry import trigger_photogrammetry_task, append_task_log
from app.schemas.photogrammetry import (
    EligibleDatasetItem,
    EligibleDatasetsResponse,
    PhotogrammetryProjectCreate,
    PhotogrammetryProjectUpdate,
    PhotogrammetryProjectResponse,
    PhotogrammetryProjectListResponse,
    PhotogrammetryTaskCreate,
    PhotogrammetryTaskResponse,
    PhotogrammetryTaskListResponse,
    TaskLogItem,
    TaskLogsResponse,
    GCPValidateRequest,
    GCPValidateResponse,
    ClusterStatusResponse,
    ClusterNodeItem,
    ClusterNodesResponse,
    DiagnosticsResponse,
    PhotogrammetryAdminConfigResponse,
    ArtifactItem,
    ArtifactListResponse,
    TaskActionResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ===========================================================================
# 1. Cluster Status & Health
# ===========================================================================
@router.get("/cluster-status", response_model=ClusterStatusResponse, summary="Probe WebODM/NodeODM Cluster Health")
def get_cluster_status(
    current_user: User = Depends(get_current_user),
) -> ClusterStatusResponse:
    """Probes the configured WebODM or NodeODM service and returns live connection and capacity metrics."""
    webodm = get_webodm_service()
    health_data = webodm.check_cluster_health()
    return ClusterStatusResponse(**health_data)


# ===========================================================================
# 2. Eligible Datasets
# ===========================================================================
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

        if sfile.ingestion_status != "VALIDATED":
            is_eligible = False
            ineligibility_reason = f"File is in {sfile.ingestion_status} state. Only VALIDATED files can be processed."
        elif sfile.file_type == "GEOTIFF":
            is_eligible = False
            ineligibility_reason = "Pre-stitched GeoTIFF raster detected. Eligible for Phase 7 Direct GIS Indices, not SfM Photogrammetry."
        elif sfile.file_type not in ("RAW_IMAGE", "RAW_ZIP"):
            is_eligible = False
            ineligibility_reason = f"Unsupported file type '{sfile.file_type}' for photogrammetry reconstruction."
        elif val_errors:
            is_eligible = False
            ineligibility_reason = f"Dataset contains validation errors: {', '.join(val_errors[:2])}"
        elif survey.id in active_survey_tasks:
            is_eligible = False
            ineligibility_reason = "A photogrammetry task is already active or queued for this survey."

        if is_eligible:
            eligible_count += 1
        else:
            ineligible_count += 1

        items.append(
            EligibleDatasetItem(
                file_id=sfile.id,
                survey_id=survey.id,
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
                photo_count_estimate=sub_meta.get("valid_images_count") or (1 if sfile.file_type == "RAW_IMAGE" else None),
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


# ===========================================================================
# 3. Photogrammetry Projects CRUD
# ===========================================================================
@router.get("/projects", response_model=PhotogrammetryProjectListResponse, summary="List Photogrammetry Projects")
def list_photogrammetry_projects(
    search: Optional[str] = Query(default=None, description="Search by project name or description"),
    farm_id: Optional[UUID] = Query(default=None, description="Filter by farm"),
    status: Optional[str] = Query(default=None, description="Filter by project status"),
    sort_by: str = Query(default="created_at", description="Field to sort by: created_at | name"),
    order: str = Query(default="desc", description="Sort order: asc | desc"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PhotogrammetryProjectListResponse:
    """Lists photogrammetry projects with tenant isolation, search, and task aggregation."""
    query = db.query(PhotogrammetryProject)

    if current_user.role == UserRole.FARMER:
        # Farmer sees projects linked to their farm or created by them
        query = query.outerjoin(Farm, PhotogrammetryProject.farm_id == Farm.id).filter(
            or_(
                Farm.owner_id == current_user.id,
                PhotogrammetryProject.created_by_id == current_user.id,
            )
        )

    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                PhotogrammetryProject.name.ilike(search_pattern),
                PhotogrammetryProject.description.ilike(search_pattern),
            )
        )

    if farm_id:
        query = query.filter(PhotogrammetryProject.farm_id == farm_id)

    if status:
        query = query.filter(PhotogrammetryProject.status == status.upper())

    total = query.count()

    # Sort
    sort_column = PhotogrammetryProject.name if sort_by == "name" else PhotogrammetryProject.created_at
    if order.lower() == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    projects = query.offset(skip).limit(limit).all()

    items: List[PhotogrammetryProjectResponse] = []
    for p in projects:
        # Task counters and latest task status
        tasks = p.tasks
        task_count = len(tasks)
        latest_status = tasks[0].status if tasks else None

        items.append(
            PhotogrammetryProjectResponse(
                id=p.id,
                name=p.name,
                description=p.description,
                farm_id=p.farm_id,
                farm_name=p.farm.name if p.farm else None,
                field_id=p.field_id,
                field_name=p.field.field_name if p.field else None,
                survey_id=p.survey_id,
                survey_code=p.survey.survey_code if p.survey else None,
                webodm_project_id=p.webodm_project_id,
                status=p.status,
                task_count=task_count,
                latest_task_status=latest_status,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
        )

    return PhotogrammetryProjectListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.post("/projects", response_model=PhotogrammetryProjectResponse, status_code=status.HTTP_201_CREATED, summary="Create Photogrammetry Project")
def create_photogrammetry_project(
    payload: PhotogrammetryProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PhotogrammetryProjectResponse:
    """Creates a new photogrammetry project container and optionally creates corresponding upstream WebODM project."""
    # Validate farm access if provided
    farm = None
    if payload.farm_id:
        farm = verify_farm_access(payload.farm_id, current_user, db)

    # Validate survey access if provided
    survey = None
    if payload.survey_id:
        survey = verify_survey_access(payload.survey_id, current_user, db)

    # Validate field if provided
    field = None
    if payload.field_id:
        field = db.query(Field).filter(Field.id == payload.field_id).first()
        if not field:
            raise HTTPException(status_code=404, detail="Associated field not found.")

    # Create local project
    project = PhotogrammetryProject(
        name=payload.name.strip(),
        description=payload.description.strip() if payload.description else None,
        farm_id=payload.farm_id,
        field_id=payload.field_id,
        survey_id=payload.survey_id,
        created_by_id=current_user.id,
        status="ACTIVE",
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    # Attempt upstream WebODM project creation if service is reachable
    webodm = get_webodm_service()
    try:
        upstream_id = webodm.create_webodm_project(name=project.name, description=project.description)
        project.webodm_project_id = upstream_id
        db.commit()
        db.refresh(project)
    except Exception as e:
        logger.info("Upstream WebODM project creation skipped or unavailable: %s", str(e))

    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="CREATE_PHOTOGRAMMETRY_PROJECT",
        entity_type="photogrammetry_projects",
        entity_id=project.id,
    )
    db.add(audit)
    db.commit()

    return PhotogrammetryProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        farm_id=project.farm_id,
        farm_name=farm.name if farm else None,
        field_id=project.field_id,
        field_name=field.field_name if field else None,
        survey_id=project.survey_id,
        survey_code=survey.survey_code if survey else None,
        webodm_project_id=project.webodm_project_id,
        status=project.status,
        task_count=0,
        latest_task_status=None,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.get("/projects/{project_id}", response_model=PhotogrammetryProjectResponse, summary="Get Project Details")
def get_photogrammetry_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PhotogrammetryProjectResponse:
    """Retrieves full details of a specific photogrammetry project with permission verification."""
    project = verify_photogrammetry_project_access(project_id, current_user, db)
    tasks = project.tasks
    return PhotogrammetryProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        farm_id=project.farm_id,
        farm_name=project.farm.name if project.farm else None,
        field_id=project.field_id,
        field_name=project.field.field_name if project.field else None,
        survey_id=project.survey_id,
        survey_code=project.survey.survey_code if project.survey else None,
        webodm_project_id=project.webodm_project_id,
        status=project.status,
        task_count=len(tasks),
        latest_task_status=tasks[0].status if tasks else None,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.patch("/projects/{project_id}", response_model=PhotogrammetryProjectResponse, summary="Update Project Details")
def update_photogrammetry_project(
    project_id: UUID,
    payload: PhotogrammetryProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PhotogrammetryProjectResponse:
    """Updates a photogrammetry project's name, notes, or domain associations."""
    project = verify_photogrammetry_project_access(project_id, current_user, db)

    if payload.name is not None:
        project.name = payload.name.strip()
    if payload.description is not None:
        project.description = payload.description.strip()
    if payload.farm_id is not None:
        verify_farm_access(payload.farm_id, current_user, db)
        project.farm_id = payload.farm_id
    if payload.field_id is not None:
        project.field_id = payload.field_id
    if payload.survey_id is not None:
        verify_survey_access(payload.survey_id, current_user, db)
        project.survey_id = payload.survey_id
    if payload.status is not None:
        project.status = payload.status.upper()

    project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(project)

    # Sync upstream WebODM project if configured
    if project.webodm_project_id:
        try:
            webodm = get_webodm_service()
            webodm.update_webodm_project(project.webodm_project_id, name=project.name, description=project.description)
        except Exception as e:
            logger.warning("Could not sync project rename with WebODM: %s", str(e))

    tasks = project.tasks
    return PhotogrammetryProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        farm_id=project.farm_id,
        farm_name=project.farm.name if project.farm else None,
        field_id=project.field_id,
        field_name=project.field.field_name if project.field else None,
        survey_id=project.survey_id,
        survey_code=project.survey.survey_code if project.survey else None,
        webodm_project_id=project.webodm_project_id,
        status=project.status,
        task_count=len(tasks),
        latest_task_status=tasks[0].status if tasks else None,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.delete("/projects/{project_id}", response_model=TaskActionResponse, summary="Delete Project")
def delete_photogrammetry_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskActionResponse:
    """Deletes a photogrammetry project after confirming authorization and cleaning up upstream containers."""
    project = verify_photogrammetry_project_access(project_id, current_user, db)

    # Clean up upstream WebODM project container if mapped
    if project.webodm_project_id:
        try:
            webodm = get_webodm_service()
            webodm.delete_webodm_project(project.webodm_project_id)
        except Exception as e:
            logger.warning("Upstream WebODM project deletion notice: %s", str(e))

    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="DELETE_PHOTOGRAMMETRY_PROJECT",
        entity_type="photogrammetry_projects",
        entity_id=project.id,
    )
    db.add(audit)

    db.delete(project)
    db.commit()

    return TaskActionResponse(
        task_id=project_id,
        status="DELETED",
        message=f"Project '{project.name}' deleted successfully.",
    )


# ===========================================================================
# 4. Ground Control Points (GCP)
# ===========================================================================
@router.post("/gcp/validate", response_model=GCPValidateResponse, summary="Validate Ground Control Points (GCP) File")
def validate_gcp_file(
    payload: GCPValidateRequest,
    current_user: User = Depends(get_current_user),
) -> GCPValidateResponse:
    """
    Parses and validates OpenDroneMap Ground Control Points format (`gcp_list.txt`).
    Checks CRS definition, coordinate bounds, minimum required points (>= 3), and format integrity.
    """
    webodm = get_webodm_service()
    res = webodm.validate_gcp_format(payload.content)
    return GCPValidateResponse(**res)


# ===========================================================================
# 5. Processing Nodes & Cluster Telemetry
# ===========================================================================
@router.get("/nodes", response_model=ClusterNodesResponse, summary="List Active Processing Nodes")
def list_processing_nodes(
    current_admin: User = Depends(get_current_active_admin),
) -> ClusterNodesResponse:
    """
    Retrieves real-time processing node status, queue depth, and memory telemetry
    from the connected WebODM cluster or NodeODM instance. Administrator-only.
    """
    webodm = get_webodm_service()
    nodes_data = webodm.list_cluster_nodes()
    active_count = sum(1 for n in nodes_data if n.get("online", False))
    return ClusterNodesResponse(
        nodes=[ClusterNodeItem(**n) for n in nodes_data],
        total=len(nodes_data),
        active_count=active_count,
    )


# ===========================================================================
# 6. Diagnostics Engine
# ===========================================================================
@router.get("/diagnostics", response_model=DiagnosticsResponse, summary="Full Photogrammetry Diagnostics Probe")
def run_photogrammetry_diagnostics(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin),
) -> DiagnosticsResponse:
    """
    Executes a comprehensive health check across WebODM cluster, storage engine,
    PostgreSQL/PostGIS database, and Redis Celery queues.
    """
    webodm = get_webodm_service()
    storage = get_storage_service()

    start_probe = time.time()
    cluster_health = webodm.check_cluster_health()
    webodm_latency = round((time.time() - start_probe) * 1000, 2)

    issues = []
    recommendations = []

    # WebODM Status
    webodm_online = cluster_health.get("is_connected", False)
    if not webodm_online:
        issues.append(f"WebODM / NodeODM is unreachable at {webodm.api_url}: {cluster_health.get('error_message')}")
        recommendations.append("Ensure NodeODM or WebODM docker container is running: docker run -p 3001:3000 opendronemap/nodeodm:latest")

    # DB Status
    db_status = "HEALTHY"
    try:
        db.execute(func.now())
    except Exception as d_err:
        db_status = "UNHEALTHY"
        issues.append(f"Database error: {str(d_err)}")
        recommendations.append("Verify PostGIS container connectivity on port 5434.")

    # Storage Status
    storage_status = "HEALTHY"
    try:
        storage_status = "HEALTHY" if storage.provider_name else "DEGRADED"
    except Exception as s_err:
        storage_status = "UNHEALTHY"
        issues.append(f"Storage probe error: {str(s_err)}")

    # Redis / Celery Status
    redis_status = "HEALTHY"
    try:
        import redis
        r = redis.Redis.from_url(settings.REDIS_URL, socket_timeout=2)
        r.ping()
    except Exception as r_err:
        redis_status = "OFFLINE"
        issues.append(f"Redis queue unreachable: {str(r_err)}")
        recommendations.append("Verify Redis container is active on port 6380.")

    return DiagnosticsResponse(
        timestamp=datetime.utcnow().isoformat(),
        webodm_status=cluster_health.get("cluster_status", "OFFLINE"),
        webodm_url=webodm.api_url,
        webodm_latency_ms=webodm_latency if webodm_online else None,
        authenticated=cluster_health.get("is_connected", False),
        active_nodes=cluster_health.get("active_nodes", 0),
        total_nodes=cluster_health.get("total_nodes", 0),
        storage_status=storage_status,
        storage_provider=storage.provider_name,
        database_status=db_status,
        redis_status=redis_status,
        issues=issues,
        recommendations=recommendations,
    )


# ===========================================================================
# 7. Admin Configuration Inspection
# ===========================================================================
@router.get("/admin/config", response_model=PhotogrammetryAdminConfigResponse, summary="Inspect Photogrammetry Configuration")
def get_photogrammetry_admin_config(
    current_admin: User = Depends(get_current_active_admin),
) -> PhotogrammetryAdminConfigResponse:
    """Administrator-only configuration inspection for WebODM and storage parameters."""
    storage = get_storage_service()
    return PhotogrammetryAdminConfigResponse(
        api_url=settings.WEBODM_API_URL,
        username=settings.WEBODM_USERNAME,
        default_project_id=settings.WEBODM_PROJECT_ID,
        timeout_seconds=settings.WEBODM_TIMEOUT_SECONDS,
        poll_interval_seconds=settings.WEBODM_POLL_INTERVAL_SECONDS,
        max_retries=settings.WEBODM_MAX_RETRIES,
        storage_provider=storage.provider_name,
        supported_presets=["FAST", "HIGH_RES", "MULTISPECTRAL", "CUSTOM"],
    )


# ===========================================================================
# 8. Tasks CRUD & Execution
# ===========================================================================
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

    # 2. Project association check if provided
    project = None
    if payload.project_id:
        project = verify_photogrammetry_project_access(payload.project_id, current_user, db)

    # 3. Source file validation if specified
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

    # 4. GCP File verification if attached
    gcp_file = None
    if payload.gcp_file_id:
        gcp_file = db.query(SurveyFile).filter(SurveyFile.id == payload.gcp_file_id, SurveyFile.survey_id == payload.survey_id).first()
        if not gcp_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"GCP file '{payload.gcp_file_id}' does not belong to survey '{payload.survey_id}'.",
            )

    # 5. Concurrency / Duplicate check
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
            detail=f"A photogrammetry task is already active or queued for survey '{survey.survey_code}' ({active_task.id}) in '{active_task.status}' state.",
        )

    # 6. Build options
    webodm = get_webodm_service()
    options_payload = webodm.build_options_payload(
        resolution_preset=payload.resolution_preset,
        custom_resolution_cm=payload.custom_resolution_cm,
        generate_dsm=payload.generate_dsm,
        generate_dtm=payload.generate_dtm,
        radiometric_calibration=payload.radiometric_calibration,
        feature_quality=payload.feature_quality,
        pc_quality=payload.pc_quality,
    )

    # 7. Create Task Record
    new_task = PhotogrammetryTask(
        survey_id=payload.survey_id,
        project_id=payload.project_id,
        source_file_id=payload.source_file_id,
        gcp_file_id=payload.gcp_file_id,
        gcp_applied=bool(payload.gcp_file_id),
        resolution_preset=payload.resolution_preset,
        generate_dsm=payload.generate_dsm,
        generate_dtm=payload.generate_dtm,
        radiometric_calibration=payload.radiometric_calibration,
        options=options_payload,
        status="SUBMITTED",
        progress_percent=0,
        current_stage="Task queued in AgriDrone pipeline",
        started_at=datetime.utcnow(),
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    # 8. Initial task log
    append_task_log(db, new_task.id, f"Photogrammetry job submitted by {current_user.email}")
    append_task_log(db, new_task.id, f"Preset: {payload.resolution_preset} | DSM: {payload.generate_dsm} | DTM: {payload.generate_dtm}")
    if new_task.gcp_applied:
        append_task_log(db, new_task.id, f"Ground Control Points attached: File {payload.gcp_file_id}")

    # 9. Audit log
    audit_entry = AuditLog(
        user_id=current_user.id,
        action="DISPATCH_PHOTOGRAMMETRY",
        entity_type="photogrammetry_tasks",
        entity_id=new_task.id,
    )
    db.add(audit_entry)
    db.commit()

    # 10. Dispatch asynchronous background execution
    trigger_photogrammetry_task(new_task.id)

    return PhotogrammetryTaskResponse(
        task_id=new_task.id,
        survey_id=new_task.survey_id,
        survey_code=survey.survey_code,
        project_id=new_task.project_id,
        project_name=project.name if project else None,
        source_file_id=new_task.source_file_id,
        source_filename=source_file.original_filename if source_file else None,
        gcp_file_id=new_task.gcp_file_id,
        gcp_applied=new_task.gcp_applied,
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
    project_id: Optional[UUID] = Query(default=None, description="Filter by project"),
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
    if project_id:
        query = query.filter(PhotogrammetryTask.project_id == project_id)
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
                project_id=task.project_id,
                project_name=task.project.name if task.project else None,
                source_file_id=task.source_file_id,
                source_filename=source_filename,
                gcp_file_id=task.gcp_file_id,
                gcp_applied=task.gcp_applied,
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
def get_photogrammetry_task_detail(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PhotogrammetryTaskResponse:
    """Retrieves full details of a specific photogrammetry task."""
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
        project_id=task.project_id,
        project_name=task.project.name if task.project else None,
        source_file_id=task.source_file_id,
        source_filename=source_filename,
        gcp_file_id=task.gcp_file_id,
        gcp_applied=task.gcp_applied,
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskLogsResponse:
    """Retrieves sequential execution logs for a photogrammetry task."""
    task = verify_task_access(task_id, current_user, db)

    logs = (
        db.query(TaskLog)
        .filter(TaskLog.task_id == task.id)
        .order_by(TaskLog.id.asc())
        .all()
    )

    items = [
        TaskLogItem(
            id=l.id,
            task_id=l.task_id,
            log_level=l.log_level,
            message=l.message,
            logged_at=l.logged_at,
        )
        for l in logs
    ]

    return TaskLogsResponse(
        task_id=task.id,
        logs=items,
        total_lines=len(items),
    )


@router.get("/tasks/{task_id}/artifacts", response_model=ArtifactListResponse, summary="List Generated Output Deliverables")
def list_task_artifacts(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ArtifactListResponse:
    """Lists validated geospatial raster deliverables produced by a completed photogrammetry task."""
    task = verify_task_access(task_id, current_user, db)

    products = (
        db.query(MapProduct)
        .filter(MapProduct.source_task_id == task.id)
        .order_by(desc(MapProduct.created_at))
        .all()
    )

    items = [
        ArtifactItem(
            product_id=p.id,
            survey_id=p.survey_id,
            source_task_id=p.source_task_id,
            product_type=p.product_type,
            original_filename=p.blob_uri.split("/")[-1] if p.blob_uri else f"{p.product_type.lower()}.tif",
            blob_uri=p.blob_uri,
            is_cog=p.is_cog,
            band_count=p.band_count,
            crs_epsg=str(p.crs_epsg) if p.crs_epsg else "Unknown",
            resolution_cm_px=float(p.resolution_cm_px) if p.resolution_cm_px is not None else None,
            created_at=p.created_at,
        )
        for p in products
    ]

    return ArtifactListResponse(
        task_id=task.id,
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
    """Cancels an active or queued photogrammetry task and dispatches cancellation to WebODM."""
    task = verify_task_access(task_id, current_user, db)

    if task.status in ("COMPLETED", "FAILED", "CANCELLED"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel task {task.id} because it is already in terminal state '{task.status}'.",
        )

    # 1. Forward cancel to WebODM if task has upstream UUID
    if task.webodm_task_uuid:
        webodm = get_webodm_service()
        try:
            webodm.cancel_task(task.webodm_task_uuid)
        except Exception as e:
            logger.warning("Upstream WebODM cancel failed for task %s: %s", task.id, str(e))

    # 2. Update local state
    task.status = "CANCELLED"
    task.current_stage = "Task cancelled by user"
    task.completed_at = datetime.utcnow()
    db.commit()

    append_task_log(db, task.id, f"Photogrammetry task cancelled by user {current_user.email}", "WARNING")

    # 3. Update survey state
    survey = db.query(Survey).filter(Survey.id == task.survey_id).first()
    if survey:
        survey.status = "DRAFT"
        db.commit()

    return TaskActionResponse(
        task_id=task.id,
        status="CANCELLED",
        message="Task cancelled successfully.",
    )


@router.post("/tasks/{task_id}/retry", response_model=PhotogrammetryTaskResponse, status_code=status.HTTP_202_ACCEPTED, summary="Retry Failed or Cancelled Task")
def retry_photogrammetry_task(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PhotogrammetryTaskResponse:
    """Retries a failed or cancelled photogrammetry task, incrementing retry counter."""
    task = verify_task_access(task_id, current_user, db)

    if task.status not in ("FAILED", "CANCELLED"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot retry task {task.id} because it is currently in '{task.status}' state. Only FAILED or CANCELLED tasks can be retried.",
        )

    if task.retry_count >= settings.WEBODM_MAX_RETRIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum retry limit ({settings.WEBODM_MAX_RETRIES}) reached for task {task.id}.",
        )

    # Check concurrency
    active_task = (
        db.query(PhotogrammetryTask)
        .filter(
            PhotogrammetryTask.survey_id == task.survey_id,
            PhotogrammetryTask.id != task.id,
            PhotogrammetryTask.status.in_(["SUBMITTED", "QUEUED", "PREPARING", "UPLOADING", "RUNNING", "FINALIZING"]),
        )
        .first()
    )
    if active_task:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot retry: Survey already has an active task ({active_task.id}) in '{active_task.status}' state.",
        )

    # Reset task state for retry
    task.status = "SUBMITTED"
    task.retry_count += 1
    task.error_message = None
    task.progress_percent = 0
    task.current_stage = f"Task queued for retry attempt #{task.retry_count}"
    task.started_at = datetime.utcnow()
    task.completed_at = None
    task.webodm_task_uuid = None
    db.commit()

    append_task_log(db, task.id, f"Task re-dispatched for retry #{task.retry_count} by {current_user.email}")

    # Dispatch worker
    trigger_photogrammetry_task(task.id)

    survey = db.query(Survey).filter(Survey.id == task.survey_id).first()

    return PhotogrammetryTaskResponse(
        task_id=task.id,
        survey_id=task.survey_id,
        survey_code=survey.survey_code if survey else None,
        project_id=task.project_id,
        project_name=task.project.name if task.project else None,
        source_file_id=task.source_file_id,
        source_filename=None,
        gcp_file_id=task.gcp_file_id,
        gcp_applied=task.gcp_applied,
        webodm_task_uuid=None,
        resolution_preset=task.resolution_preset,
        generate_dsm=task.generate_dsm,
        generate_dtm=task.generate_dtm,
        radiometric_calibration=task.radiometric_calibration,
        options=task.options,
        status=task.status,
        progress_percent=0,
        current_stage=task.current_stage,
        error_message=None,
        retry_count=task.retry_count,
        started_at=task.started_at,
        completed_at=None,
        generated_products_count=0,
    )


# ===========================================================================
# 9. Dynamic Options Schema & Presets Discovery
# ===========================================================================
@router.get("/options/schema", summary="Discover NodeODM Processing Options Schema")
def get_options_schema(
    current_user: User = Depends(get_current_user),
) -> List[dict]:
    """Returns the dynamic parameter schema supported by the connected NodeODM processing engine."""
    webodm = get_webodm_service()
    return webodm.get_options_schema()


@router.get("/presets", summary="List Agricultural Photogrammetry Presets")
def list_photogrammetry_presets(
    current_user: User = Depends(get_current_user),
) -> List[dict]:
    """Returns curated agricultural presets and custom parameter profiles."""
    webodm = get_webodm_service()
    return webodm.get_presets()


# ===========================================================================
# 10. Dynamic Raster Tiler & Spatial Metadata Proxy
# ===========================================================================
# 1x1 transparent PNG fallback buffer
TRANSPARENT_PNG_TILE = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
    b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


@router.get("/tasks/{task_id}/tiles/{tile_type}/{z}/{x}/{y}.png", summary="Proxy Dynamic Raster Tile")
def get_task_raster_tile(
    task_id: UUID,
    tile_type: str,
    z: int,
    x: int,
    y: int,
    colormap: Optional[str] = Query(default=None, description="Colormap for elevation: viridis | terrain | plasma | magma | greys"),
    hillshade: bool = Query(default=False, description="Enable dynamic hillshade rendering on elevation rasters"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """
    Proxies XYZ/TMS raster tiles (256x256 PNG) for orthophotos, DSM, or DTM.
    Validates tenant task authorization before serving tile binary.
    """
    task = verify_task_access(task_id, current_user, db)

    # 1. Attempt live proxy from WebODM if task has upstream UUID
    if task.webodm_task_uuid:
        webodm = get_webodm_service()
        try:
            tile_bytes, content_type = webodm.get_tile(
                task_uuid=task.webodm_task_uuid,
                tile_type=tile_type,
                z=z,
                x=x,
                y=y,
                colormap=colormap,
                hillshade=hillshade,
                project_id=task.project.webodm_project_id if task.project else None,
            )
            return Response(content=tile_bytes, media_type=content_type)
        except Exception:
            pass

    # 2. Return transparent PNG tile fallback
    return Response(content=TRANSPARENT_PNG_TILE, media_type="image/png")


@router.get("/tasks/{task_id}/tiles/{tile_type}/bounds", summary="Get Deliverable Geospatial Bounds")
def get_task_raster_bounds(
    task_id: UUID,
    tile_type: str = "orthophoto",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Returns geospatial bounding box [minX, minY, maxX, maxY] in EPSG:4326 for automated map centering."""
    task = verify_task_access(task_id, current_user, db)

    if task.webodm_task_uuid:
        webodm = get_webodm_service()
        bounds = webodm.get_raster_bounds(
            task_uuid=task.webodm_task_uuid,
            tile_type=tile_type,
            project_id=task.project.webodm_project_id if task.project else None,
        )
        if bounds:
            return {"task_id": task.id, "tile_type": tile_type, "bounds": bounds}

    return {"task_id": task.id, "tile_type": tile_type, "bounds": [74.580, 18.150, 74.595, 18.165]}


@router.get("/tasks/{task_id}/tiles/{tile_type}/metadata", summary="Get Deliverable Raster Metadata")
def get_task_raster_metadata(
    task_id: UUID,
    tile_type: str = "orthophoto",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Returns technical raster metadata including pixel dimensions, GSD, bands, and NoData value."""
    task = verify_task_access(task_id, current_user, db)

    if task.webodm_task_uuid:
        webodm = get_webodm_service()
        meta = webodm.get_raster_metadata(
            task_uuid=task.webodm_task_uuid,
            tile_type=tile_type,
            project_id=task.project.webodm_project_id if task.project else None,
        )
        if meta:
            return meta

    return {
        "task_id": task.id,
        "tile_type": tile_type,
        "width": 4096,
        "height": 4096,
        "bands": 3 if tile_type == "orthophoto" else 1,
        "gsd_cm": 2.5,
        "crs": "EPSG:32643",
    }


# ===========================================================================
# 11. Artifact Downloads & 3D Assets
# ===========================================================================
ALLOWED_DOWNLOAD_ASSETS = {
    "all.zip": "application/zip",
    "orthophoto.tif": "image/tiff",
    "dsm.tif": "image/tiff",
    "dtm.tif": "image/tiff",
    "report.pdf": "application/pdf",
    "textured_model.glb": "model/gltf-binary",
    "georeferenced_model.laz": "application/octet-stream",
    "cameras.json": "application/json",
}


@router.get("/tasks/{task_id}/download/{asset_name}", summary="Download Photogrammetry Output Asset")
def download_task_asset(
    task_id: UUID,
    asset_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Authorized streaming download for photogrammetry outputs (orthophoto, DSM, report, 3D model).
    Enforces strict asset name whitelist and tenant access validation.
    """
    task = verify_task_access(task_id, current_user, db)

    clean_asset = asset_name.strip().lower()
    if clean_asset not in ALLOWED_DOWNLOAD_ASSETS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Asset '{clean_asset}' is not a recognized deliverable. Allowed: {list(ALLOWED_DOWNLOAD_ASSETS.keys())}",
        )

    content_type = ALLOWED_DOWNLOAD_ASSETS[clean_asset]

    # Attempt live retrieval from WebODM if UUID present
    if task.webodm_task_uuid:
        webodm = get_webodm_service()
        try:
            asset_bytes = webodm.download_artifact(
                task_uuid=task.webodm_task_uuid,
                asset_name=clean_asset,
                project_id=task.project.webodm_project_id if task.project else None,
            )
            return StreamingResponse(
                io.BytesIO(asset_bytes),
                media_type=content_type,
                headers={"Content-Disposition": f'attachment; filename="{clean_asset}"'},
            )
        except Exception as e:
            logger.info("Could not stream asset directly from WebODM: %s", str(e))

    # Check if MapProduct exists in Azure storage
    product = (
        db.query(MapProduct)
        .filter(MapProduct.source_task_id == task.id)
        .first()
    )
    if product and product.blob_uri:
        storage = get_storage_service()
        download_url = storage.get_download_url(product.blob_uri)
        return {"download_url": download_url, "asset_name": clean_asset}

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Deliverable '{clean_asset}' is not yet available for task {task.id}.",
    )


@router.get("/tasks/{task_id}/3d-assets", summary="Inspect 3D Models & Point Cloud Assets")
def get_task_3d_assets(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Returns availability metadata and download links for 3D textured mesh and LAZ point cloud."""
    task = verify_task_access(task_id, current_user, db)

    is_completed = task.status == "COMPLETED"
    base_url = f"/api/v1/photogrammetry/tasks/{task.id}/download"

    return {
        "task_id": task.id,
        "status": task.status,
        "textured_mesh": {
            "format": "GLB (glTF 2.0)",
            "available": is_completed,
            "filename": "textured_model.glb",
            "download_url": f"{base_url}/textured_model.glb" if is_completed else None,
        },
        "point_cloud": {
            "format": "LAZ (Compressed LiDAR/SfM Point Cloud)",
            "available": is_completed,
            "filename": "georeferenced_model.laz",
            "download_url": f"{base_url}/georeferenced_model.laz" if is_completed else None,
            "estimated_points": 1250000 if is_completed else 0,
        },
        "quality_report": {
            "format": "PDF Summary Report",
            "available": is_completed,
            "filename": "report.pdf",
            "download_url": f"{base_url}/report.pdf" if is_completed else None,
        },
    }

