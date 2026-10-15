"""Background Worker & Task Dispatcher for Phase 7 Raster Analytics.

Executes asynchronous multi-algorithm batch jobs, handles state transitions,
validates inputs, writes Cloud-Optimized GeoTIFFs, uploads artifacts to storage,
and registers MapProduct and ZonalStatistic database records.
"""

import os
import shutil
import tempfile
import logging
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID

import numpy as np
import rasterio

from app.core.celery_app import celery_app
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.product import AlgorithmJob, MapProduct, ZonalStatistic
from app.models.survey import Survey
from app.services.storage import get_storage_service, build_blob_path
from app.services.raster_analytics import (
    RasterAnalyticsService,
    NODATA_VALUE_FLOAT32,
    RasterAnalyticsError,
)

logger = logging.getLogger(__name__)


def _resolve_source_raster_path(storage, product: MapProduct, temp_dir: str) -> str:
    """Safely resolves the local filesystem path for a MapProduct raster.

    If stored locally, uses safe path; if Azure blob, downloads to temp file.
    """
    blob_uri = product.blob_uri
    if blob_uri.startswith("local://"):
        # Format: local://{container}/{blob_path}
        parts = blob_uri.replace("local://", "").split("/", 1)
        container = parts[0]
        blob_path = parts[1] if len(parts) > 1 else ""
        if hasattr(storage, "_resolve_safe_path"):
            return storage._resolve_safe_path(container, blob_path)
        raise ValueError(f"Storage service cannot resolve local path for {blob_uri}")

    # Azure blob or remote stream: download to temporary file
    container = settings.AZURE_CONTAINER_ORTHO
    # Parse container and blob_path from blob_uri
    blob_path = blob_uri.split(f"{container}/")[-1] if f"{container}/" in blob_uri else os.path.basename(blob_uri)

    logger.info("Downloading remote raster blob %s/%s to temporary storage...", container, blob_path)
    content = storage.download_file(container, blob_path)
    local_temp = os.path.join(temp_dir, f"source_{product.id}.tif")
    with open(local_temp, "wb") as f:
        f.write(content)
    return local_temp


def execute_algorithm_batch_workflow(batch_id_str: str):
    """Core synchronous workflow executed by Celery worker or background thread.

    Processes all AlgorithmJobs associated with the given batch_id.
    """
    batch_id = UUID(batch_id_str)
    db = SessionLocal()
    storage = get_storage_service()
    temp_dir = tempfile.mkdtemp(prefix=f"agridrone_batch_{batch_id_str[:8]}_")

    try:
        # 1. Fetch all jobs in this batch
        jobs: List[AlgorithmJob] = (
            db.query(AlgorithmJob)
            .filter(AlgorithmJob.batch_id == batch_id)
            .order_by(AlgorithmJob.started_at.asc())
            .all()
        )

        if not jobs:
            logger.error("No algorithm jobs found for batch_id %s", batch_id)
            return

        # Mark all jobs as PREPARING
        for job in jobs:
            job.status = "PREPARING"
            job.current_stage = "Inspecting source raster & validating spectral channels"
            job.progress_percent = 10
            job.started_at = datetime.utcnow()
        db.commit()

        # 2. Identify input product
        input_product_id = jobs[0].input_product_id
        input_product: Optional[MapProduct] = (
            db.query(MapProduct).filter(MapProduct.id == input_product_id).first()
        )

        if not input_product:
            for job in jobs:
                job.status = "FAILED"
                job.error_message = f"Input raster MapProduct {input_product_id} not found."
                job.completed_at = datetime.utcnow()
            db.commit()
            return

        survey: Optional[Survey] = (
            db.query(Survey).filter(Survey.id == input_product.survey_id).first()
        )

        # 3. Resolve source raster file
        try:
            source_raster_path = _resolve_source_raster_path(storage, input_product, temp_dir)
            if not os.path.exists(source_raster_path):
                raise FileNotFoundError(f"Source raster file not accessible at {source_raster_path}")
        except Exception as e:
            logger.exception("Failed to access source raster for batch %s: %s", batch_id, str(e))
            for job in jobs:
                job.status = "FAILED"
                job.error_message = f"Failed to access source raster: {str(e)}"
                job.completed_at = datetime.utcnow()
            db.commit()
            return

        # 4. Inspect source raster
        try:
            inspection = RasterAnalyticsService.inspect_raster(source_raster_path)
            logger.info(
                "Source raster inspected: %dx%d, %d bands, Sensor: %s, CRS: %s",
                inspection.width,
                inspection.height,
                inspection.band_count,
                inspection.detected_sensor,
                inspection.crs_epsg,
            )
        except Exception as e:
            for job in jobs:
                job.status = "FAILED"
                job.error_message = f"Source raster inspection failed: {str(e)}"
                job.completed_at = datetime.utcnow()
            db.commit()
            return

        # 5. Open source raster to read required band arrays
        with rasterio.open(source_raster_path) as src:
            source_profile = src.profile.copy()
            source_nodatavals = src.nodatavals
            pixel_res_m = (abs(src.transform[0]) + abs(src.transform[4])) / 2.0
            if not src.crs or not src.crs.is_projected:
                # If geographic (EPSG:4326), convert degrees to approx meters
                pixel_res_m = pixel_res_m * 111320.0

            # 6. Process each algorithm job
            for job in jobs:
                algo_code = job.algorithm_code.upper()
                params = job.parameters or {}
                band_mapping = params.get("band_mapping") or inspection.suggested_band_mapping

                logger.info("Processing job %s (Algorithm: %s)...", job.id, algo_code)
                job.status = "VALIDATING"
                job.current_stage = f"Validating spectral band mapping for {algo_code}"
                job.progress_percent = 20
                db.commit()

                # Validate band mapping
                is_valid, validation_err = RasterAnalyticsService.validate_band_mapping(
                    band_count=inspection.band_count,
                    mapping=band_mapping,
                    algorithm_code=algo_code,
                )

                if not is_valid:
                    logger.warning("Job %s rejected: %s", job.id, validation_err)
                    job.status = "FAILED"
                    job.error_message = validation_err
                    job.completed_at = datetime.utcnow()
                    db.commit()
                    continue

                # Band mapping is valid -> proceed to RUNNING
                job.status = "RUNNING"
                job.current_stage = f"Loading spectral bands and computing {algo_code}"
                job.progress_percent = 40
                db.commit()

                try:
                    # Read needed bands
                    spec = RasterAnalyticsService.ALGORITHM_SPECS[algo_code]
                    required_bands = spec["required_bands"]
                    band_arrays: Dict[str, np.ndarray] = {}
                    source_nodata_mask = np.zeros((src.height, src.width), dtype=bool)

                    for b_name in required_bands:
                        b_idx = band_mapping[b_name]
                        arr = src.read(b_idx)
                        band_arrays[b_name] = arr

                        # Accumulate NoData mask from source
                        nd_val = source_nodatavals[b_idx - 1]
                        if nd_val is not None:
                            source_nodata_mask |= (arr == nd_val)

                    # Compute index array
                    index_arr, valid_mask, calc_stats = RasterAnalyticsService.compute_index(
                        band_arrays=band_arrays,
                        algorithm_code=algo_code,
                        parameters=params,
                        source_nodata_mask=source_nodata_mask,
                    )

                    if calc_stats["valid_pixel_count"] == 0:
                        raise RasterAnalyticsError(
                            f"Computation produced 0 valid pixels. Denominators were zero or all inputs were NoData."
                        )

                    job.progress_percent = 65
                    job.current_stage = "Writing Cloud-Optimized GeoTIFF & calculating zonal statistics"
                    db.commit()

                    # Calculate Zonal Vigour Statistics
                    zonal_stats = RasterAnalyticsService.calculate_zonal_statistics(
                        index_array=index_arr,
                        valid_mask=valid_mask,
                        algorithm_code=algo_code,
                        pixel_res_m=pixel_res_m,
                    )

                    # Write temporary GeoTIFF
                    out_filename = f"{algo_code.lower()}_{job.id}.tif"
                    local_out_path = os.path.join(temp_dir, out_filename)
                    metadata_tags = {
                        "ALGORITHM": algo_code,
                        "FORMULA": spec["formula"],
                        "PARAMETERS": str(params),
                        "BAND_MAPPING": str(band_mapping),
                        "SOURCE_PRODUCT_ID": str(input_product.id),
                        "SURVEY_ID": str(input_product.survey_id),
                        "PROCESSED_AT": datetime.utcnow().isoformat(),
                        "SOFTWARE": "AgriDrone AutoMap Phase 7 Engine (Rasterio/GDAL/NumPy)",
                    }

                    RasterAnalyticsService.write_geotiff(
                        output_path=local_out_path,
                        index_array=index_arr,
                        source_profile=source_profile,
                        metadata_tags=metadata_tags,
                    )

                    # Validate written GeoTIFF
                    is_out_valid, out_summary, out_err = RasterAnalyticsService.validate_output_geotiff(
                        output_path=local_out_path,
                        expected_algo=algo_code,
                    )

                    if not is_out_valid:
                        raise RasterAnalyticsError(f"Output raster validation failed: {out_err}")

                    job.status = "STORING"
                    job.current_stage = "Uploading index raster to secure storage & registering map product"
                    job.progress_percent = 85
                    db.commit()

                    # Upload to storage
                    blob_path = build_blob_path(
                        prefix=f"surveys/{input_product.survey_id}/indices",
                        filename=out_filename,
                    )

                    with open(local_out_path, "rb") as f_out:
                        upload_res = storage.upload_file(
                            file_obj=f_out,
                            container=settings.AZURE_CONTAINER_INDICES,
                            blob_path=blob_path,
                            content_type="image/tiff",
                        )

                    # Register MapProduct
                    map_product = MapProduct(
                        survey_id=input_product.survey_id,
                        source_job_id=job.id,
                        product_type=f"INDEX_{algo_code}",
                        blob_uri=upload_res["blob_uri"],
                        is_cog=True,
                        band_count=1,
                        crs_epsg=inspection.crs_epsg or "EPSG:4326",
                        resolution_cm_px=inspection.gsd_cm,
                        extent_geom=input_product.extent_geom,
                        statistical_summary={
                            **calc_stats,
                            **out_summary,
                            "provenance": {
                                "source_product_id": str(input_product.id),
                                "source_blob_uri": input_product.blob_uri,
                                "algorithm": algo_code,
                                "formula": spec["formula"],
                                "parameters": params,
                                "band_mapping": band_mapping,
                                "radiometric_type": inspection.radiometric_type,
                                "calibration_notes": inspection.calibration_notes,
                                "processed_at": datetime.utcnow().isoformat(),
                            },
                        },
                        is_published=False,
                    )
                    db.add(map_product)
                    db.flush()  # Acquire map_product.id

                    # Register Zonal Statistics
                    for z_stat in zonal_stats:
                        zs = ZonalStatistic(
                            map_product_id=map_product.id,
                            zone_name=z_stat["zone_name"],
                            min_val=z_stat["min_val"],
                            max_val=z_stat["max_val"],
                            area_hectares=z_stat["area_hectares"],
                            area_percentage=z_stat["area_percentage"],
                        )
                        db.add(zs)

                    # Mark Job COMPLETED
                    job.status = "COMPLETED"
                    job.output_product_id = map_product.id
                    job.progress_percent = 100
                    job.current_stage = f"Index product {algo_code} generated and registered successfully"
                    job.completed_at = datetime.utcnow()
                    db.commit()
                    logger.info("Successfully completed job %s for %s", job.id, algo_code)

                except Exception as job_exc:
                    logger.exception("Error processing algorithm %s on job %s: %s", algo_code, job.id, str(job_exc))
                    db.rollback()
                    # Re-fetch job to update status cleanly
                    failed_job = db.query(AlgorithmJob).filter(AlgorithmJob.id == job.id).first()
                    if failed_job:
                        failed_job.status = "FAILED"
                        failed_job.error_message = f"Processing error: {str(job_exc)}"
                        failed_job.completed_at = datetime.utcnow()
                        db.commit()

    except Exception as fatal_e:
        logger.exception("Fatal unhandled exception in batch %s: %s", batch_id_str, str(fatal_e))
        try:
            failed_jobs = db.query(AlgorithmJob).filter(AlgorithmJob.batch_id == batch_id).all()
            for fj in failed_jobs:
                if fj.status not in ("COMPLETED", "FAILED"):
                    fj.status = "FAILED"
                    fj.error_message = f"Fatal batch coordinator error: {str(fatal_e)}"
                    fj.completed_at = datetime.utcnow()
            db.commit()
        except Exception:
            pass
    finally:
        db.close()
        # Clean up temporary directory
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning("Could not clean up temp dir %s: %s", temp_dir, str(e))


@celery_app.task(name="app.tasks.raster_analytics.dispatch_algorithm_batch", bind=True, max_retries=2)
def dispatch_algorithm_batch(self, batch_id_str: str):
    """Celery worker task for executing raster algorithm batch processing."""
    try:
        execute_algorithm_batch_workflow(batch_id_str)
    except Exception as exc:
        logger.error("Celery algorithm batch exception: %s. Retrying...", str(exc))
        raise self.retry(exc=exc, countdown=5)


def trigger_algorithm_batch(batch_id: UUID, use_celery: bool = True) -> bool:
    """Dispatches algorithm batch via Celery worker, with automatic background thread fallback."""
    batch_id_str = str(batch_id)
    if use_celery:
        try:
            res = dispatch_algorithm_batch.delay(batch_id_str)
            logger.info("Dispatched algorithm batch %s via Celery (Celery Task ID: %s)", batch_id_str, res.id)
            return True
        except Exception as e:
            logger.warning("Celery dispatch unavailable (%s). Falling back to background worker thread.", str(e))

    thread = threading.Thread(
        target=execute_algorithm_batch_workflow,
        args=(batch_id_str,),
        daemon=True,
        name=f"Raster-Worker-{batch_id_str[:8]}",
    )
    thread.start()
    logger.info("Launched algorithm batch %s in background worker thread.", batch_id_str)
    return True
