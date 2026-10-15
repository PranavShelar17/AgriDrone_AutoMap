import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union
import bcrypt
import jwt

from app.core.config import settings

logger = logging.getLogger(__name__)

TOKEN_ISSUER = "agridrone-automap"
TOKEN_AUDIENCE = "agridrone-portal"


def get_password_hash(password: str) -> str:
    """
    Generate secure bcrypt hash for password.
    """
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify plain password against stored bcrypt hash with timing-attack resistance.
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception as e:
        logger.warning("Password verification failed with error: %s", str(e))
        return False


def create_access_token(
    subject: Union[str, Any, Dict[str, Any]],
    role: Optional[str] = None,
    email: Optional[str] = None,
    full_name: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create signed HS256 JWT access token with standard claims."""
    if isinstance(subject, dict):
        sub_val = str(subject.get("sub", ""))
        role_val = subject.get("role", role or "ADMIN")
        email_val = subject.get("email", email or "")
        name_val = subject.get("name", full_name or "")
        expires_delta = subject.get("expires_delta", expires_delta)
    else:
        sub_val = str(subject)
        role_val = role or "ADMIN"
        email_val = email or ""
        name_val = full_name or ""

    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: Dict[str, Any] = {
        "sub": sub_val,
        "role": role_val,
        "email": email_val,
        "name": name_val,
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "iss": TOKEN_ISSUER,
        "aud": TOKEN_AUDIENCE,
    }

    encoded_jwt = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and strictly validate signature, expiration, issuer, and audience.
    Returns payload dictionary or None if invalid or expired.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            issuer=TOKEN_ISSUER,
            audience=TOKEN_AUDIENCE,
            options={"require": ["exp", "sub", "role", "iss", "aud"]},
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.debug("JWT validation failed: Token has expired.")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning("JWT validation failed: %s", str(e))
        return None
