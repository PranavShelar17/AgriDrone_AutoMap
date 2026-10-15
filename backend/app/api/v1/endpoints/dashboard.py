from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.tenant import User, UserRole
from app.models.farm import Farm, Field
from app.models.survey import Survey
from app.models.file import SurveyFile
from app.services.storage import get_storage_service
from app.schemas.dashboard import (
    DashboardStatsResponse,
    RecentSurveyItem,
    RecentUploadItem,
    RecentFailureItem,
)

router = APIRouter()


@router.get("/stats", response_model=DashboardStatsResponse, summary="Retrieve real database dashboard metrics")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardStatsResponse:
    if current_user.role == UserRole.FARMER:
        # Strict isolation for farmer: scope all counts and lists to their assigned farms
        farm_ids = [f.id for f in db.query(Farm.id).filter(Farm.owner_id == current_user.id).all()]
        field_ids = [f.id for f in db.query(Field.id).filter(Field.farm_id.in_(farm_ids)).all()] if farm_ids else []
        survey_ids = [s.id for s in db.query(Survey.id).filter(Survey.field_id.in_(field_ids)).all()] if field_ids else []

        total_farms = len(farm_ids)
        total_fields = len(field_ids)
        total_surveys = len(survey_ids)

        files_base = db.query(SurveyFile).filter(SurveyFile.survey_id.in_(survey_ids)) if survey_ids else db.query(SurveyFile).filter(False)
        total_datasets = files_base.count()
        awaiting_validation = files_base.filter(SurveyFile.ingestion_status.in_(["PENDING", "VALIDATING"])).count()
        validated_datasets = files_base.filter(SurveyFile.ingestion_status == "VALIDATED").count()
        rejected_datasets = files_base.filter(SurveyFile.ingestion_status == "REJECTED").count()

        recent_surveys_db = (
            db.query(Survey)
            .filter(Survey.id.in_(survey_ids))
            .order_by(Survey.created_at.desc())
            .limit(5)
            .all()
            if survey_ids else []
        )
        recent_files_db = (
            files_base.order_by(SurveyFile.created_at.desc()).limit(5).all()
            if survey_ids else []
        )
        failures_db = (
            files_base.filter(SurveyFile.ingestion_status == "REJECTED")
            .order_by(SurveyFile.created_at.desc())
            .limit(5)
            .all()
            if survey_ids else []
        )
    else:
        total_farms = db.query(func.count(Farm.id)).scalar() or 0
        total_fields = db.query(func.count(Field.id)).scalar() or 0
        total_surveys = db.query(func.count(Survey.id)).scalar() or 0
        total_datasets = db.query(func.count(SurveyFile.id)).scalar() or 0

        awaiting_validation = (
            db.query(func.count(SurveyFile.id))
            .filter(SurveyFile.ingestion_status.in_(["PENDING", "VALIDATING"]))
            .scalar()
            or 0
        )
        validated_datasets = (
            db.query(func.count(SurveyFile.id))
            .filter(SurveyFile.ingestion_status == "VALIDATED")
            .scalar()
            or 0
        )
        rejected_datasets = (
            db.query(func.count(SurveyFile.id))
            .filter(SurveyFile.ingestion_status == "REJECTED")
            .scalar()
            or 0
        )

        recent_surveys_db = (
            db.query(Survey)
            .order_by(Survey.created_at.desc())
            .limit(5)
            .all()
        )
        recent_files_db = (
            db.query(SurveyFile)
            .order_by(SurveyFile.created_at.desc())
            .limit(5)
            .all()
        )
        failures_db = (
            db.query(SurveyFile)
            .filter(SurveyFile.ingestion_status == "REJECTED")
            .order_by(SurveyFile.created_at.desc())
            .limit(5)
            .all()
        )

    storage = get_storage_service()
    recent_surveys = []
    for s in recent_surveys_db:
        f_stats = (
            db.query(
                func.count(SurveyFile.id).label("count"),
                func.coalesce(func.sum(SurveyFile.file_size_bytes), 0).label("bytes"),
            )
            .filter(SurveyFile.survey_id == s.id)
            .first()
        )
        recent_surveys.append(
            RecentSurveyItem(
                survey_id=s.id,
                survey_code=s.survey_code,
                farm_name=s.field.farm.name if s.field and s.field.farm else "Unknown Farm",
                field_name=s.field.field_name if s.field else "Unknown Field",
                flight_date=s.flight_date,
                sensor_type=s.sensor_type,
                status=s.status,
                files_count=f_stats.count if f_stats else 0,
                total_bytes=int(f_stats.bytes) if f_stats else 0,
                created_at=s.created_at,
            )
        )

    # Recent uploads
    recent_files_db = (
        db.query(SurveyFile)
        .order_by(SurveyFile.created_at.desc())
        .limit(5)
        .all()
    )
    recent_uploads = []
    for f in recent_files_db:
        meta = f.validation_metadata or {}
        recent_uploads.append(
            RecentUploadItem(
                file_id=f.id,
                survey_id=f.survey_id,
                survey_code=f.survey.survey_code if f.survey else "Unknown",
                original_filename=f.original_filename,
                file_type=f.file_type,
                file_size_bytes=f.file_size_bytes,
                ingestion_status=f.ingestion_status,
                workflow_route=meta.get("workflow_route", "NONE"),
                created_at=f.created_at,
            )
        )

    # Recent failures requiring attention
    failures_db = (
        db.query(SurveyFile)
        .filter(SurveyFile.ingestion_status == "REJECTED")
        .order_by(SurveyFile.created_at.desc())
        .limit(5)
        .all()
    )
    recent_failures = []
    for f in failures_db:
        meta = f.validation_metadata or {}
        recent_failures.append(
            RecentFailureItem(
                file_id=f.id,
                survey_id=f.survey_id,
                survey_code=f.survey.survey_code if f.survey else "Unknown",
                original_filename=f.original_filename,
                file_size_bytes=f.file_size_bytes,
                validation_errors=meta.get("validation_errors", ["Validation failure."]),
                created_at=f.created_at,
            )
        )

    return DashboardStatsResponse(
        total_farms=total_farms,
        total_fields=total_fields,
        total_surveys=total_surveys,
        total_datasets=total_datasets,
        datasets_awaiting_validation=awaiting_validation,
        datasets_validated=validated_datasets,
        datasets_rejected=rejected_datasets,
        storage_provider=storage.provider_name,
        recent_surveys=recent_surveys,
        recent_uploads=recent_uploads,
        recent_failures=recent_failures,
    )
