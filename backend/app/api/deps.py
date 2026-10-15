import json
import logging
import uuid
from typing import Any, Dict, Generator, Optional
from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from shapely.geometry import Polygon, mapping, shape
from geoalchemy2.shape import from_shape, to_shape

from app.core.config import settings
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.audit import AuditLog
from app.models.farm import Farm, Field
from app.models.product import AlgorithmJob, MapProduct
from app.models.report import Report
from app.models.survey import Survey
from app.models.task import PhotogrammetryTask
from app.models.tenant import User, UserRole

logger = logging.getLogger(__name__)

DEFAULT_DEV_ADMIN_EMAIL = "admin@agridrone.local"


def get_current_user(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(default=None),
    cookie_token: Optional[str] = Cookie(default=None, alias=settings.AUTH_COOKIE_NAME),
) -> User:
    """
    Authenticate request via Bearer JWT token or HttpOnly session cookie.
    Validates token signature, expiration, and user account status.
    Rejects unauthenticated requests with HTTP 401.
    """
    token: Optional[str] = None
    if authorization:
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format. Expected 'Bearer <token>'.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token = authorization.split(" ", 1)[1].strip()
    elif cookie_token:
        token = cookie_token

    if token:
        payload = decode_access_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired access token.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token payload missing subject identifier.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        try:
            user_uuid = uuid.UUID(user_id_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Malformed subject identifier in token.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user = db.query(User).filter(User.id == user_uuid).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account not found.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account has been deactivated. Please contact your system administrator.",
            )
        return user

    # No token provided
    if settings.ENVIRONMENT != "development" or settings.REQUIRE_AUTHENTICATION:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Fallback in local development only when REQUIRE_AUTHENTICATION is explicitly False
    user = db.query(User).filter(User.email == DEFAULT_DEV_ADMIN_EMAIL).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Default development user not initialized.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_current_user_with_query_fallback(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(default=None),
    cookie_token: Optional[str] = Cookie(default=None, alias=settings.AUTH_COOKIE_NAME),
    token: Optional[str] = None,
) -> User:
    """
    Authenticates request with support for query parameter token fallback (e.g. MapLibre raster tiles).
    """
    effective_auth = authorization
    if not effective_auth and not cookie_token and token:
        effective_auth = f"Bearer {token}"
    return get_current_user(db=db, authorization=effective_auth, cookie_token=cookie_token)


def get_current_active_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Enforce that current authenticated user has administrative privileges."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required for this action.",
        )
    return current_user


# ---------------------------------------------------------------------------
# Granular Resource Ownership & Access Validation (Mitigates IDOR completely)
# ---------------------------------------------------------------------------

def verify_farm_access(farm_id: uuid.UUID, user: User, db: Session) -> Farm:
    """Validate farm exists and is accessible by the authenticated user."""
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Farm {farm_id} does not exist or was not found.")
    if user.role in (UserRole.ADMIN, UserRole.AGRONOMIST) or farm.owner_id == user.id:
        return farm
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Farm {farm_id} does not exist or was not found.")


def verify_field_access(field_id: uuid.UUID, user: User, db: Session) -> Field:
    """Validate field exists and belongs to a farm accessible by the authenticated user."""
    field = db.query(Field).join(Farm).filter(Field.id == field_id).first()
    if not field:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Field {field_id} does not exist or was not found.")
    if user.role in (UserRole.ADMIN, UserRole.AGRONOMIST) or field.farm.owner_id == user.id:
        return field
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Field {field_id} does not exist or was not found.")


def verify_survey_access(survey_id: uuid.UUID, user: User, db: Session) -> Survey:
    """Validate survey exists and belongs to a field/farm accessible by the user."""
    survey = db.query(Survey).join(Field).join(Farm).filter(Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Survey {survey_id} does not exist or was not found.")
    if user.role in (UserRole.ADMIN, UserRole.AGRONOMIST) or survey.field.farm.owner_id == user.id:
        return survey
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Survey {survey_id} does not exist or was not found.")


def verify_map_product_access(product_id: uuid.UUID, user: User, db: Session) -> MapProduct:
    """Validate map product exists and belongs to a survey accessible by the user."""
    product = db.query(MapProduct).join(Survey).join(Field).join(Farm).filter(MapProduct.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Map product {product_id} not found.")
    if user.role in (UserRole.ADMIN, UserRole.AGRONOMIST) or product.survey.field.farm.owner_id == user.id:
        return product
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Map product {product_id} not found.")


def verify_task_access(task_id: uuid.UUID, user: User, db: Session) -> PhotogrammetryTask:
    """Validate photogrammetry task exists and belongs to a survey accessible by the user."""
    task = db.query(PhotogrammetryTask).join(Survey).join(Field).join(Farm).filter(PhotogrammetryTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {task_id} not found.")
    if user.role in (UserRole.ADMIN, UserRole.AGRONOMIST) or task.survey.field.farm.owner_id == user.id:
        return task
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {task_id} not found.")


def verify_algorithm_job_access(job_id: uuid.UUID, user: User, db: Session) -> AlgorithmJob:
    """Validate algorithm job exists and belongs to an input product accessible by the user."""
    job = (
        db.query(AlgorithmJob)
        .join(MapProduct, AlgorithmJob.input_product_id == MapProduct.id)
        .join(Survey)
        .join(Field)
        .join(Farm)
        .filter(AlgorithmJob.id == job_id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Algorithm job {job_id} not found.")
    if user.role in (UserRole.ADMIN, UserRole.AGRONOMIST) or job.input_product.survey.field.farm.owner_id == user.id:
        return job
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Algorithm job {job_id} not found.")


def verify_report_access(report_id: uuid.UUID, user: User, db: Session) -> Report:
    """Validate report exists and belongs to a survey accessible by the user."""
    report = db.query(Report).join(Survey).join(Field).join(Farm).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report {report_id} not found.")
    if user.role in (UserRole.ADMIN, UserRole.AGRONOMIST) or report.survey.field.farm.owner_id == user.id:
        return report
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report {report_id} not found.")


# ---------------------------------------------------------------------------
# Spatial validation utilities
# ---------------------------------------------------------------------------

def validate_and_convert_geojson_polygon(geojson_dict: Optional[Dict[str, Any]]) -> Optional[Any]:
    """
    Validate GeoJSON Polygon input using Shapely and return a GeoAlchemy2 WKBElement with SRID 4326.
    Raises HTTPException 422 if geometry is invalid or out of WGS84 bounds.
    """
    if not geojson_dict:
        return None

    try:
        geom = shape(geojson_dict)
        if not isinstance(geom, Polygon):
            raise HTTPException(
                status_code=422,
                detail=f"Geometry must be a Polygon, received: {geom.geom_type}",
            )

        if not geom.is_valid:
            geom = geom.buffer(0)
            if not geom.is_valid or not isinstance(geom, Polygon):
                raise HTTPException(
                    status_code=422,
                    detail="Supplied polygon boundary is self-intersecting or topologically invalid.",
                )

        minx, miny, maxx, maxy = geom.bounds
        if minx < -180.0 or maxx > 180.0 or miny < -90.0 or maxy > 90.0:
            raise HTTPException(
                status_code=422,
                detail="Coordinates exceed valid WGS84 geographical bounds (Longitude [-180, 180], Latitude [-90, 90]).",
            )

        return from_shape(geom, srid=4326)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid GeoJSON polygon structure: {str(e)}",
        )


def convert_geometry_to_geojson(geom_wkb: Any) -> Optional[Dict[str, Any]]:
    """Convert PostGIS WKBElement back to GeoJSON dict."""
    if geom_wkb is None:
        return None
    try:
        shapely_geom = to_shape(geom_wkb)
        return mapping(shapely_geom)
    except Exception as e:
        logger.warning("Failed to serialize geometry to GeoJSON: %s", e)
        return None
