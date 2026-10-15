import time
import socket
from urllib.parse import urlparse
from fastapi import APIRouter, Response, status
from sqlalchemy import text
from app.core.config import settings
from app.db.session import SessionLocal
from app.schemas.health import HealthResponse, ReadinessResponse, ComponentStatus

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
def liveness_check() -> HealthResponse:
    """
    Liveness probe: returns 200 OK if the FastAPI process is running and accepting HTTP requests.
    Used by Kubernetes / Docker container health checks.
    """
    return HealthResponse(
        status="ok",
        version="0.1.0",
        environment=settings.ENVIRONMENT
    )


@router.get(
    "/health/readiness",
    response_model=ReadinessResponse,
    responses={
        200: {"description": "All required dependencies are operational."},
        503: {"description": "One or more critical dependencies (Database, Redis) are unavailable."}
    },
    tags=["Health"]
)
def readiness_check(response: Response) -> ReadinessResponse:
    """
    Readiness probe: verifies connectivity to PostgreSQL (with PostGIS) and Redis.
    Does not expose sensitive credentials or full connection strings.
    """
    components = {}
    is_ready = True

    # 1. Check PostgreSQL & PostGIS
    db_start = time.perf_counter()
    try:
        db = SessionLocal()
        try:
            # Check basic connection and spatial extension
            row = db.execute(text("SELECT PostGIS_Version();")).fetchone()
            db_latency = (time.perf_counter() - db_start) * 1000
            postgis_ver = row[0] if row else "unknown"
            components["database"] = ComponentStatus(
                status="healthy",
                latency_ms=round(db_latency, 2),
                details=f"PostgreSQL with PostGIS {postgis_ver.split()[0]}"
            )
        finally:
            db.close()
    except Exception as e:
        db_latency = (time.perf_counter() - db_start) * 1000
        is_ready = False
        components["database"] = ComponentStatus(
            status="unhealthy",
            latency_ms=round(db_latency, 2),
            details="Connection failed to database service"
        )

    # 2. Check Redis
    redis_start = time.perf_counter()
    try:
        parsed_redis = urlparse(settings.REDIS_URL)
        redis_host = parsed_redis.hostname or "localhost"
        redis_port = parsed_redis.port or 6379

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2.0)
        sock.connect((redis_host, redis_port))
        sock.sendall(b"PING\r\n")
        reply = sock.recv(32)
        sock.close()

        redis_latency = (time.perf_counter() - redis_start) * 1000
        if b"PONG" in reply:
            components["redis"] = ComponentStatus(
                status="healthy",
                latency_ms=round(redis_latency, 2),
                details="Redis broker responsive"
            )
        else:
            is_ready = False
            components["redis"] = ComponentStatus(
                status="unhealthy",
                latency_ms=round(redis_latency, 2),
                details="Invalid Redis PING response"
            )
    except Exception:
        redis_latency = (time.perf_counter() - redis_start) * 1000
        is_ready = False
        components["redis"] = ComponentStatus(
            status="unhealthy",
            latency_ms=round(redis_latency, 2),
            details="Connection failed to Redis broker"
        )

    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ReadinessResponse(
        status="ready" if is_ready else "not_ready",
        components=components
    )
