import uuid
import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.api.deps import (
    get_current_user,
    verify_field_access,
    verify_survey_access,
    validate_and_convert_geojson_polygon,
    convert_geometry_to_geojson,
)
from app.models.tenant import User, UserRole
from app.models.farm import Farm, Field
from app.models.survey import Survey
from app.models.file import SurveyFile
from app.schemas.survey import (
    SurveyCreate,
    SurveyUpdate,
    SurveyResponse,
    SurveyDetailResponse,
    SurveyListResponse,
    SurveyFileBrief,
)

router = APIRouter()


def _generate_survey_code(db: Session, flight_date: datetime.date) -> str:
    """Generate human-readable unique survey code: SRV-YYYY-XXX."""
    year = flight_date.year
    prefix = f"SRV-{year}-"
    count = db.query(func.count(Survey.id)).filter(Survey.survey_code.like(f"{prefix}%")).scalar() or 0
    seq = count + 1
    # Check for uniqueness
    while True:
        code = f"{prefix}{seq:03d}"
        exists = db.query(Survey.id).filter(Survey.survey_code == code).first()
        if not exists:
            return code
        seq += 1


@router.get("", response_model=SurveyListResponse, summary="List surveys with pagination and filtering")
def list_surveys(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    field_id: Optional[uuid.UUID] = Query(None, description="Filter by target field"),
    farm_id: Optional[uuid.UUID] = Query(None, description="Filter by parent farm"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by survey status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SurveyListResponse:
    query = db.query(Survey).join(Field, Field.id == Survey.field_id).join(Farm, Farm.id == Field.farm_id)

    # Enforce farmer isolation: farmers only see surveys for their assigned farms
    if current_user.role == UserRole.FARMER:
        query = query.filter(Farm.owner_id == current_user.id)

    if field_id:
        query = query.filter(Survey.field_id == field_id)
    if farm_id:
        query = query.filter(Field.farm_id == farm_id)
    if status_filter:
        query = query.filter(Survey.status == status_filter.upper())

    total = query.count()
    surveys = query.order_by(Survey.flight_date.desc(), Survey.created_at.desc()).offset(skip).limit(limit).all()

    items = []
    for s in surveys:
        f_stats = (
            db.query(
                func.count(SurveyFile.id).label("count"),
                func.coalesce(func.sum(SurveyFile.file_size_bytes), 0).label("bytes"),
            )
            .filter(SurveyFile.survey_id == s.id)
            .first()
        )
        file_count = f_stats.count if f_stats else 0
        total_bytes = int(f_stats.bytes) if f_stats else 0

        items.append(
            SurveyResponse(
                id=s.id,
                field_id=s.field_id,
                farm_name=s.field.farm.name if s.field and s.field.farm else None,
                field_name=s.field.field_name if s.field else None,
                survey_code=s.survey_code,
                flight_date=s.flight_date,
                drone_model=s.drone_model,
                sensor_type=s.sensor_type,
                flight_altitude_m=float(s.flight_altitude_m) if s.flight_altitude_m else None,
                status=s.status,
                coverage_geojson=convert_geometry_to_geojson(s.coverage_geom),
                created_at=s.created_at,
                files_count=file_count,
                total_bytes=total_bytes,
            )
        )

    return SurveyListResponse(items=items, total=total, skip=skip, limit=limit)


@router.post("", response_model=SurveyResponse, status_code=status.HTTP_201_CREATED, summary="Create a new survey")
def create_survey(
    survey_in: SurveyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SurveyResponse:
    field = verify_field_access(survey_in.field_id, current_user, db)

    survey_code = survey_in.survey_code.strip() if survey_in.survey_code else _generate_survey_code(db, survey_in.flight_date)

    # Check survey_code uniqueness
    existing = db.query(Survey).filter(Survey.survey_code == survey_code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Survey code '{survey_code}' is already registered.",
        )

    coverage_geom = validate_and_convert_geojson_polygon(survey_in.coverage_geojson)

    survey = Survey(
        field_id=field.id,
        survey_code=survey_code,
        flight_date=survey_in.flight_date,
        drone_model=survey_in.drone_model.strip() if survey_in.drone_model else "DJI Mavic 3 Enterprise",
        sensor_type=survey_in.sensor_type.strip().upper(),
        flight_altitude_m=survey_in.flight_altitude_m,
        status="DRAFT",
        coverage_geom=coverage_geom,
    )
    db.add(survey)
    db.commit()
    db.refresh(survey)

    return SurveyResponse(
        id=survey.id,
        field_id=survey.field_id,
        farm_name=field.farm.name if field.farm else None,
        field_name=field.field_name,
        survey_code=survey.survey_code,
        flight_date=survey.flight_date,
        drone_model=survey.drone_model,
        sensor_type=survey.sensor_type,
        flight_altitude_m=float(survey.flight_altitude_m) if survey.flight_altitude_m else None,
        status=survey.status,
        coverage_geojson=convert_geometry_to_geojson(survey.coverage_geom),
        created_at=survey.created_at,
        files_count=0,
        total_bytes=0,
    )


@router.get("/{survey_id}", response_model=SurveyDetailResponse, summary="Get survey details and associated files")
def get_survey(
    survey_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SurveyDetailResponse:
    survey = verify_survey_access(survey_id, current_user, db)

    files = db.query(SurveyFile).filter(SurveyFile.survey_id == survey.id).order_by(SurveyFile.created_at.desc()).all()
    file_briefs = []
    total_bytes = 0
    for f in files:
        total_bytes += f.file_size_bytes
        file_briefs.append(
            SurveyFileBrief(
                id=f.id,
                original_filename=f.original_filename,
                file_type=f.file_type,
                file_size_bytes=f.file_size_bytes,
                mime_type=f.mime_type,
                ingestion_status=f.ingestion_status,
                created_at=f.created_at,
                validation_metadata=f.validation_metadata,
            )
        )

    return SurveyDetailResponse(
        id=survey.id,
        field_id=survey.field_id,
        farm_name=survey.field.farm.name if survey.field and survey.field.farm else None,
        field_name=survey.field.field_name if survey.field else None,
        survey_code=survey.survey_code,
        flight_date=survey.flight_date,
        drone_model=survey.drone_model,
        sensor_type=survey.sensor_type,
        flight_altitude_m=float(survey.flight_altitude_m) if survey.flight_altitude_m else None,
        status=survey.status,
        coverage_geojson=convert_geometry_to_geojson(survey.coverage_geom),
        created_at=survey.created_at,
        files_count=len(file_briefs),
        total_bytes=total_bytes,
        files=file_briefs,
    )


@router.put("/{survey_id}", response_model=SurveyResponse, summary="Update survey metadata")
def update_survey(
    survey_id: uuid.UUID,
    survey_in: SurveyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SurveyResponse:
    survey = verify_survey_access(survey_id, current_user, db)

    if survey_in.survey_code is not None:
        survey.survey_code = survey_in.survey_code.strip()
    if survey_in.flight_date is not None:
        survey.flight_date = survey_in.flight_date
    if survey_in.drone_model is not None:
        survey.drone_model = survey_in.drone_model.strip()
    if survey_in.sensor_type is not None:
        survey.sensor_type = survey_in.sensor_type.strip().upper()
    if survey_in.flight_altitude_m is not None:
        survey.flight_altitude_m = survey_in.flight_altitude_m
    if survey_in.status is not None:
        survey.status = survey_in.status.strip().upper()
    if survey_in.coverage_geojson is not None:
        survey.coverage_geom = validate_and_convert_geojson_polygon(survey_in.coverage_geojson)

    db.commit()
    db.refresh(survey)

    f_stats = (
        db.query(
            func.count(SurveyFile.id).label("count"),
            func.coalesce(func.sum(SurveyFile.file_size_bytes), 0).label("bytes"),
        )
        .filter(SurveyFile.survey_id == survey.id)
        .first()
    )

    return SurveyResponse(
        id=survey.id,
        field_id=survey.field_id,
        farm_name=survey.field.farm.name if survey.field and survey.field.farm else None,
        field_name=survey.field.field_name if survey.field else None,
        survey_code=survey.survey_code,
        flight_date=survey.flight_date,
        drone_model=survey.drone_model,
        sensor_type=survey.sensor_type,
        flight_altitude_m=float(survey.flight_altitude_m) if survey.flight_altitude_m else None,
        status=survey.status,
        coverage_geojson=convert_geometry_to_geojson(survey.coverage_geom),
        created_at=survey.created_at,
        files_count=f_stats.count if f_stats else 0,
        total_bytes=int(f_stats.bytes) if f_stats else 0,
    )


@router.delete("/{survey_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Cancel/delete a survey")
def delete_survey(
    survey_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.FARMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Farmers are not permitted to delete survey records. Contact an administrator.",
        )
    survey = verify_survey_access(survey_id, current_user, db)

    db.delete(survey)
    db.commit()
    return None
