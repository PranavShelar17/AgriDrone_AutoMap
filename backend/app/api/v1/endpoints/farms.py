import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.api.deps import (
    get_current_user,
    verify_farm_access,
    validate_and_convert_geojson_polygon,
    convert_geometry_to_geojson,
)
from app.models.tenant import User, UserRole
from app.models.farm import Farm, Field
from app.models.survey import Survey
from app.schemas.farm import (
    FarmCreate,
    FarmUpdate,
    FarmResponse,
    FarmListResponse,
    FieldCreate,
    FieldUpdate,
    FieldResponse,
)

router = APIRouter()


@router.get("", response_model=FarmListResponse, summary="List registered farms with pagination and search")
def list_farms(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by farm name, village, or district"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FarmListResponse:
    query = db.query(Farm)

    # Enforce farmer isolation: farmers only see farms they own
    if current_user.role == UserRole.FARMER:
        query = query.filter(Farm.owner_id == current_user.id)

    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            (Farm.name.ilike(search_pattern))
            | (Farm.village.ilike(search_pattern))
            | (Farm.district.ilike(search_pattern))
            | (Farm.state.ilike(search_pattern))
        )

    total = query.count()
    farms = query.order_by(Farm.created_at.desc()).offset(skip).limit(limit).all()

    items = []
    for farm in farms:
        f_count = db.query(func.count(Field.id)).filter(Field.farm_id == farm.id).scalar() or 0
        s_count = (
            db.query(func.count(Survey.id))
            .join(Field, Field.id == Survey.field_id)
            .filter(Field.farm_id == farm.id)
            .scalar()
            or 0
        )
        items.append(
            FarmResponse(
                id=farm.id,
                owner_id=farm.owner_id,
                name=farm.name,
                village=farm.village,
                district=farm.district,
                state=farm.state,
                boundary_geojson=convert_geometry_to_geojson(farm.boundary_geom),
                fields_count=f_count,
                surveys_count=s_count,
                created_at=farm.created_at,
            )
        )

    return FarmListResponse(items=items, total=total, skip=skip, limit=limit)


@router.post("", response_model=FarmResponse, status_code=status.HTTP_201_CREATED, summary="Register a new farm")
def create_farm(
    farm_in: FarmCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FarmResponse:
    boundary_geom = validate_and_convert_geojson_polygon(farm_in.boundary_geojson)

    farm = Farm(
        owner_id=current_user.id,
        name=farm_in.name.strip(),
        village=farm_in.village.strip() if farm_in.village else None,
        district=farm_in.district.strip() if farm_in.district else None,
        state=farm_in.state.strip() if farm_in.state else None,
        boundary_geom=boundary_geom,
    )
    db.add(farm)
    db.commit()
    db.refresh(farm)

    return FarmResponse(
        id=farm.id,
        owner_id=farm.owner_id,
        name=farm.name,
        village=farm.village,
        district=farm.district,
        state=farm.state,
        boundary_geojson=convert_geometry_to_geojson(farm.boundary_geom),
        fields_count=0,
        surveys_count=0,
        created_at=farm.created_at,
    )


@router.get("/{farm_id}", response_model=FarmResponse, summary="Get farm details and associated fields")
def get_farm(
    farm_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FarmResponse:
    farm = verify_farm_access(farm_id, current_user, db)

    fields = db.query(Field).filter(Field.farm_id == farm.id).order_by(Field.created_at.desc()).all()
    fields_list = []
    for f in fields:
        s_count = db.query(func.count(Survey.id)).filter(Survey.field_id == f.id).scalar() or 0
        fields_list.append(
            FieldResponse(
                id=f.id,
                farm_id=f.farm_id,
                field_name=f.field_name,
                crop_type=f.crop_type,
                area_hectares=float(f.area_hectares) if f.area_hectares else None,
                boundary_geojson=convert_geometry_to_geojson(f.boundary_geom),
                surveys_count=s_count,
                created_at=f.created_at,
            )
        )

    s_count_total = (
        db.query(func.count(Survey.id))
        .join(Field, Field.id == Survey.field_id)
        .filter(Field.farm_id == farm.id)
        .scalar()
        or 0
    )

    return FarmResponse(
        id=farm.id,
        owner_id=farm.owner_id,
        name=farm.name,
        village=farm.village,
        district=farm.district,
        state=farm.state,
        boundary_geojson=convert_geometry_to_geojson(farm.boundary_geom),
        fields_count=len(fields_list),
        surveys_count=s_count_total,
        created_at=farm.created_at,
        fields=fields_list,
    )


@router.put("/{farm_id}", response_model=FarmResponse, summary="Update farm metadata")
def update_farm(
    farm_id: uuid.UUID,
    farm_in: FarmUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FarmResponse:
    farm = verify_farm_access(farm_id, current_user, db)

    if farm_in.name is not None:
        farm.name = farm_in.name.strip()
    if farm_in.village is not None:
        farm.village = farm_in.village.strip() if farm_in.village else None
    if farm_in.district is not None:
        farm.district = farm_in.district.strip() if farm_in.district else None
    if farm_in.state is not None:
        farm.state = farm_in.state.strip() if farm_in.state else None
    if farm_in.boundary_geojson is not None:
        farm.boundary_geom = validate_and_convert_geojson_polygon(farm_in.boundary_geojson)

    db.commit()
    db.refresh(farm)

    f_count = db.query(func.count(Field.id)).filter(Field.farm_id == farm.id).scalar() or 0
    s_count = (
        db.query(func.count(Survey.id))
        .join(Field, Field.id == Survey.field_id)
        .filter(Field.farm_id == farm.id)
        .scalar()
        or 0
    )

    return FarmResponse(
        id=farm.id,
        owner_id=farm.owner_id,
        name=farm.name,
        village=farm.village,
        district=farm.district,
        state=farm.state,
        boundary_geojson=convert_geometry_to_geojson(farm.boundary_geom),
        fields_count=f_count,
        surveys_count=s_count,
        created_at=farm.created_at,
    )


@router.delete("/{farm_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete farm and associated records")
def delete_farm(
    farm_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.FARMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Farmers are not permitted to delete farm records. Contact an administrator.",
        )
    farm = verify_farm_access(farm_id, current_user, db)

    db.delete(farm)
    db.commit()
    return None


# --- Field Sub-endpoints ---


@router.get("/{farm_id}/fields", response_model=List[FieldResponse], summary="List fields for a specific farm")
def list_fields_for_farm(
    farm_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[FieldResponse]:
    farm = verify_farm_access(farm_id, current_user, db)

    fields = db.query(Field).filter(Field.farm_id == farm_id).order_by(Field.created_at.desc()).all()
    results = []
    for f in fields:
        s_count = db.query(func.count(Survey.id)).filter(Survey.field_id == f.id).scalar() or 0
        results.append(
            FieldResponse(
                id=f.id,
                farm_id=f.farm_id,
                field_name=f.field_name,
                crop_type=f.crop_type,
                area_hectares=float(f.area_hectares) if f.area_hectares else None,
                boundary_geojson=convert_geometry_to_geojson(f.boundary_geom),
                surveys_count=s_count,
                created_at=f.created_at,
            )
        )
    return results


@router.post("/{farm_id}/fields", response_model=FieldResponse, status_code=status.HTTP_201_CREATED, summary="Create a new field in a farm")
def create_field_for_farm(
    farm_id: uuid.UUID,
    field_in: FieldCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FieldResponse:
    farm = verify_farm_access(farm_id, current_user, db)

    boundary_geom = validate_and_convert_geojson_polygon(field_in.boundary_geojson)

    field = Field(
        farm_id=farm.id,
        field_name=field_in.field_name.strip(),
        crop_type=field_in.crop_type.strip() if field_in.crop_type else None,
        area_hectares=field_in.area_hectares,
        boundary_geom=boundary_geom,
    )
    db.add(field)
    db.commit()
    db.refresh(field)

    return FieldResponse(
        id=field.id,
        farm_id=field.farm_id,
        field_name=field.field_name,
        crop_type=field.crop_type,
        area_hectares=float(field.area_hectares) if field.area_hectares else None,
        boundary_geojson=convert_geometry_to_geojson(field.boundary_geom),
        surveys_count=0,
        created_at=field.created_at,
    )
