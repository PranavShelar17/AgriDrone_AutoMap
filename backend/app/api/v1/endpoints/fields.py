import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.api.deps import (
    get_current_user,
    verify_field_access,
    validate_and_convert_geojson_polygon,
    convert_geometry_to_geojson,
)
from app.models.tenant import User, UserRole
from app.models.farm import Field
from app.models.survey import Survey
from app.schemas.farm import FieldUpdate, FieldResponse

router = APIRouter()


@router.get("/{field_id}", response_model=FieldResponse, summary="Get field details")
def get_field(
    field_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FieldResponse:
    field = verify_field_access(field_id, current_user, db)

    s_count = db.query(func.count(Survey.id)).filter(Survey.field_id == field.id).scalar() or 0
    return FieldResponse(
        id=field.id,
        farm_id=field.farm_id,
        field_name=field.field_name,
        crop_type=field.crop_type,
        area_hectares=float(field.area_hectares) if field.area_hectares else None,
        boundary_geojson=convert_geometry_to_geojson(field.boundary_geom),
        surveys_count=s_count,
        created_at=field.created_at,
    )


@router.put("/{field_id}", response_model=FieldResponse, summary="Update field metadata")
def update_field(
    field_id: uuid.UUID,
    field_in: FieldUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FieldResponse:
    field = verify_field_access(field_id, current_user, db)

    if field_in.field_name is not None:
        field.field_name = field_in.field_name.strip()
    if field_in.crop_type is not None:
        field.crop_type = field_in.crop_type.strip() if field_in.crop_type else None
    if field_in.area_hectares is not None:
        field.area_hectares = field_in.area_hectares
    if field_in.boundary_geojson is not None:
        field.boundary_geom = validate_and_convert_geojson_polygon(field_in.boundary_geojson)

    db.commit()
    db.refresh(field)

    s_count = db.query(func.count(Survey.id)).filter(Survey.field_id == field.id).scalar() or 0
    return FieldResponse(
        id=field.id,
        farm_id=field.farm_id,
        field_name=field.field_name,
        crop_type=field.crop_type,
        area_hectares=float(field.area_hectares) if field.area_hectares else None,
        boundary_geojson=convert_geometry_to_geojson(field.boundary_geom),
        surveys_count=s_count,
        created_at=field.created_at,
    )


@router.delete("/{field_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete field")
def delete_field(
    field_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.FARMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Farmers are not permitted to delete fields. Contact an administrator.",
        )
    field = verify_field_access(field_id, current_user, db)

    db.delete(field)
    db.commit()
    return None
