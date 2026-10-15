"""Tasks module for AgriDrone AutoMap."""
from app.tasks.photogrammetry import (
    trigger_photogrammetry_task,
    dispatch_reconstruction,
    execute_photogrammetry_workflow,
)
from app.tasks.raster_analytics import (
    trigger_algorithm_batch,
    dispatch_algorithm_batch,
    execute_algorithm_batch_workflow,
)

__all__ = [
    "trigger_photogrammetry_task",
    "dispatch_reconstruction",
    "execute_photogrammetry_workflow",
    "trigger_algorithm_batch",
    "dispatch_algorithm_batch",
    "execute_algorithm_batch_workflow",
]
