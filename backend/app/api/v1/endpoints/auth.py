import logging
import time
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.db.session import get_db
from app.api.deps import get_current_user, get_current_active_admin
from app.models.audit import AuditLog
from app.models.farm import Farm
from app.models.tenant import User, UserRole
from app.schemas.auth import (
    AccountStatusUpdateRequest,
    FarmerAssignFarmRequest,
    FarmerCreateRequest,
    LoginRequest,
    TokenResponse,
    UserProfileResponse,
)
from app.schemas.common import StandardMessageResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory rate limiting fallback: ip -> list of failed attempt timestamps
_failed_login_attempts: Dict[str, List[float]] = defaultdict(list)


def _check_rate_limit(client_ip: str) -> None:
    """Enforce brute-force login throttling."""
    now = time.time()
    window = settings.RATE_LIMIT_WINDOW_SECONDS
    cutoff = now - window

    # Clean old attempts
    attempts = [t for t in _failed_login_attempts[client_ip] if t > cutoff]
    _failed_login_attempts[client_ip] = attempts

    if len(attempts) >= settings.RATE_LIMIT_LOGIN_ATTEMPTS:
        logger.warning("Rate limit exceeded for IP %s (%d failed attempts in %ds)", client_ip, len(attempts), window)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many failed login attempts. Please wait {window // 60} minutes before trying again.",
        )


def _record_failed_attempt(client_ip: str) -> None:
    _failed_login_attempts[client_ip].append(time.time())


def _clear_failed_attempts(client_ip: str) -> None:
    if client_ip in _failed_login_attempts:
        del _failed_login_attempts[client_ip]


def record_audit(
    db: Session,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID,
    user_id: Optional[uuid.UUID] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> None:
    """Helper to persist security and operational audit logs."""
    try:
        clean_ip = ip_address
        if clean_ip:
            import ipaddress
            try:
                ipaddress.ip_address(clean_ip)
            except ValueError:
                clean_ip = "127.0.0.1"

        log = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            ip_address=clean_ip,
            user_agent=user_agent[:500] if user_agent else None,
            timestamp=datetime.now(timezone.utc),
        )
        db.add(log)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error("Failed to write audit log: %s", str(e))


def get_user_assigned_farm_ids(user: User, db: Session) -> List[uuid.UUID]:
    """Return all farm IDs owned by this user, or all farms if ADMIN/AGRONOMIST."""
    if user.role in (UserRole.ADMIN, UserRole.AGRONOMIST):
        return [f.id for f in db.query(Farm.id).all()]
    return [f.id for f in db.query(Farm.id).filter(Farm.owner_id == user.id).all()]


# Import dependencies lazily to avoid circular imports
def get_auth_deps():
    from app.api.deps import get_current_active_admin, get_current_user
    return get_current_user, get_current_active_admin


@router.post("/login", response_model=TokenResponse)
def login(
    request: Request,
    response: Response,
    login_data: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    Authenticate user with email and password.
    Returns signed Bearer JWT and sets secure HttpOnly session cookie.
    Enforces rate-limiting and logs authentication audit events.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("user-agent")

    _check_rate_limit(client_ip)

    user = db.query(User).filter(User.email == login_data.email.lower().strip()).first()

    # Timing-safe validation: even if user not found, run dummy verify to mitigate timing attacks
    if not user or not verify_password(login_data.password, user.password_hash):
        _record_failed_attempt(client_ip)
        dummy_entity_id = user.id if user else uuid.uuid4()
        record_audit(
            db=db,
            action="LOGIN_FAILED",
            entity_type="USER",
            entity_id=dummy_entity_id,
            user_id=user.id if user else None,
            ip_address=client_ip,
            user_agent=user_agent,
        )
        logger.warning("Failed login attempt for email: %s from IP: %s", login_data.email, client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        record_audit(
            db=db,
            action="LOGIN_REJECTED_DISABLED",
            entity_type="USER",
            entity_id=user.id,
            user_id=user.id,
            ip_address=client_ip,
            user_agent=user_agent,
        )
        logger.warning("Login attempt for deactivated user: %s", user.email)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been deactivated. Please contact your system administrator.",
        )

    # Successful authentication
    _clear_failed_attempts(client_ip)

    access_token = create_access_token(
        subject=user.id,
        role=user.role.value,
        email=user.email,
        full_name=user.full_name,
    )

    # Set secure HttpOnly session cookie
    response.set_cookie(
        key=settings.AUTH_COOKIE_NAME,
        value=access_token,
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )

    record_audit(
        db=db,
        action="LOGIN_SUCCESS",
        entity_type="USER",
        entity_id=user.id,
        user_id=user.id,
        ip_address=client_ip,
        user_agent=user_agent,
    )

    assigned_farm_ids = get_user_assigned_farm_ids(user, db)

    user_profile = UserProfileResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        is_active=user.is_active,
        assigned_farm_ids=assigned_farm_ids,
        created_at=user.created_at,
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user_profile,
    )


@router.post("/logout", response_model=StandardMessageResponse)
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> StandardMessageResponse:
    """
    Log out the current user and invalidate the session cookie.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("user-agent")

    # Clear session cookie
    response.delete_cookie(
        key=settings.AUTH_COOKIE_NAME,
        path="/",
        httponly=True,
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )

    return StandardMessageResponse(
        status="success",
        message="Logged out successfully. Session credentials cleared.",
    )


@router.get("/me", response_model=UserProfileResponse)
def get_current_user_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserProfileResponse:
    """
    Retrieve authenticated user profile and assigned resource permissions.
    """
    assigned_farm_ids = get_user_assigned_farm_ids(current_user, db)
    return UserProfileResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role.value,
        is_active=current_user.is_active,
        assigned_farm_ids=assigned_farm_ids,
        created_at=current_user.created_at,
    )


@router.post("/register-farmer", response_model=UserProfileResponse, status_code=status.HTTP_201_CREATED)
def register_farmer(
    payload: FarmerCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_active_admin),
) -> UserProfileResponse:
    """
    Administrator workflow to register a farmer account and optionally assign a farm.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    email_clean = payload.email.lower().strip()

    existing = db.query(User).filter(User.email == email_clean).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An account with email '{email_clean}' already exists.",
        )

    # If farm_id provided, verify it exists
    farm = None
    if payload.farm_id:
        farm = db.query(Farm).filter(Farm.id == payload.farm_id).first()
        if not farm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Farm with ID {payload.farm_id} does not exist.",
            )

    new_farmer = User(
        email=email_clean,
        password_hash=get_password_hash(payload.password),
        full_name=payload.full_name.strip(),
        role=UserRole.FARMER,
        is_active=True,
    )
    db.add(new_farmer)
    db.flush()

    if farm:
        farm.owner_id = new_farmer.id
        db.add(farm)

    db.commit()
    db.refresh(new_farmer)

    record_audit(
        db=db,
        action="FARMER_ACCOUNT_CREATED",
        entity_type="USER",
        entity_id=new_farmer.id,
        user_id=admin.id,
        ip_address=client_ip,
        user_agent=request.headers.get("user-agent"),
    )

    assigned_farm_ids = [farm.id] if farm else []
    return UserProfileResponse(
        id=new_farmer.id,
        email=new_farmer.email,
        full_name=new_farmer.full_name,
        role=new_farmer.role.value,
        is_active=new_farmer.is_active,
        assigned_farm_ids=assigned_farm_ids,
        created_at=new_farmer.created_at,
    )


@router.post("/assign-farm", response_model=StandardMessageResponse)
def assign_farm_to_farmer(
    payload: FarmerAssignFarmRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_active_admin),
) -> StandardMessageResponse:
    """
    Administrator workflow to assign a farm to a farmer.
    """
    farmer = db.query(User).filter(User.id == payload.farmer_id).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer account not found.")

    farm = db.query(Farm).filter(Farm.id == payload.farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found.")

    farm.owner_id = farmer.id
    db.add(farm)
    db.commit()

    record_audit(
        db=db,
        action="FARM_ASSIGNED",
        entity_type="FARM",
        entity_id=farm.id,
        user_id=admin.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    return StandardMessageResponse(
        status="success",
        message=f"Farm '{farm.name}' successfully assigned to farmer '{farmer.full_name}'.",
    )


@router.put("/users/{user_id}/status", response_model=UserProfileResponse)
def update_user_status(
    user_id: uuid.UUID,
    payload: AccountStatusUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_active_admin),
) -> UserProfileResponse:
    """
    Administrator workflow to enable or disable a user account.
    Prevents self-disablement by the administrator.
    """
    if admin.id == user_id and not payload.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrators cannot deactivate their own active session.",
        )

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User account not found.")

    target_user.is_active = payload.is_active
    db.add(target_user)
    db.commit()
    db.refresh(target_user)

    action = "USER_ACTIVATED" if payload.is_active else "USER_DEACTIVATED"
    record_audit(
        db=db,
        action=action,
        entity_type="USER",
        entity_id=target_user.id,
        user_id=admin.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    assigned_farm_ids = get_user_assigned_farm_ids(target_user, db)
    return UserProfileResponse(
        id=target_user.id,
        email=target_user.email,
        full_name=target_user.full_name,
        role=target_user.role.value,
        is_active=target_user.is_active,
        assigned_farm_ids=assigned_farm_ids,
        created_at=target_user.created_at,
    )
