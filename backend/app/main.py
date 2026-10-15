from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.api.v1.api import api_router
from app.schemas.common import ErrorResponse, ErrorDetails

# Initialize structured logging
setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    description="Production-grade agricultural drone mapping, photogrammetry, and geospatial analytics platform API.",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event() -> None:
    logger.info("AgriDrone AutoMap FastAPI backend starting up in environment: %s", settings.ENVIRONMENT)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catches unhandled exceptions and formats a standardized JSON error without leaking internal secrets."""
    logger.error("Unhandled server exception: %s on path %s", exc, request.url.path, exc_info=True)
    error_payload = ErrorResponse(
        error=ErrorDetails(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected server error occurred. Please contact system support.",
            details=None
        )
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_payload.model_dump(mode="json")
    )


# Mount versioned API routes
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
def root_redirect():
    """Root redirect / information endpoint."""
    return {
        "project": settings.PROJECT_NAME,
        "version": "0.1.0",
        "status": "online",
        "docs_url": "/docs",
        "health_check": f"{settings.API_V1_STR}/health"
    }
