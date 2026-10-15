import logging
from celery import Celery
from app.core.config import settings

logger = logging.getLogger(__name__)

# Configure Celery application with Redis broker
celery_app = Celery(
    "agridrone_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.photogrammetry",
        "app.tasks.raster_analytics",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=14400,  # 4 hours max per task
    task_soft_time_limit=13800,
    worker_prefetch_multiplier=1,
    task_routes={
        "app.tasks.photogrammetry.*": {"queue": "photogrammetry"},
        "app.tasks.raster_analytics.*": {"queue": "raster_analytics"},
    },
)
