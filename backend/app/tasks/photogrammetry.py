import io
import time
import zipfile
import logging
import threading
from datetime import datetime
from typing import List, Tuple, Optional
from uuid import UUID

from app.core.celery_app import celery_app
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.task import PhotogrammetryTask, TaskLog
from app.models.file import SurveyFile
from app.models.survey import Survey
from app.models.product import MapProduct
from app.services.storage import get_storage_service
from app.services.webodm import get_webodm_service, WebODMError, WebODMConnectionError
from app.services.validation import FileValidationService

logger = logging.getLogger(__name__)


def append_task_log(db, task_id: UUID, message: str, level: str = "INFO"):
    """Helper to append structured log entries to task_logs table."""
    try:
        log_entry = TaskLog(
            task_id=task_id,
            log_level=level,
            message=message,
            logged_at=datetime.utcnow(),
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        logger.error("Failed to append task log for %s: %s", task_id, str(e))
        db.rollback()


def execute_photogrammetry_workflow(task_id_str: str):
    """Core synchronous photogrammetry execution workflow executed by worker or background thread."""
    task_id = UUID(task_id_str)
    db = SessionLocal()
    storage = get_storage_service()
    webodm = get_webodm_service()
    validator = FileValidationService()

    try:
        task = db.query(PhotogrammetryTask).filter(PhotogrammetryTask.id == task_id).first()
        if not task:
            logger.error("Photogrammetry task %s not found in database.", task_id)
            return

        survey = db.query(Survey).filter(Survey.id == task.survey_id).first()
        if not survey:
            task.status = "FAILED"
            task.error_message = f"Survey {task.survey_id} not found."
            task.completed_at = datetime.utcnow()
            db.commit()
            return

        # 1. State: PREPARING
        task.status = "PREPARING"
        task.started_at = datetime.utcnow()
        task.progress_percent = 5
        task.current_stage = "Preparing dataset & source photographs"
        survey.status = "PROCESSING"
        db.commit()

        append_task_log(db, task.id, f"Initializing photogrammetry task for survey {survey.survey_code}")
        append_task_log(db, task.id, f"Storage provider active: {storage.provider_name}")

        # 2. Gather source images
        staged_images: List[Tuple[str, bytes]] = []

        if task.source_file_id:
            source_files = db.query(SurveyFile).filter(SurveyFile.id == task.source_file_id).all()
        else:
            source_files = db.query(SurveyFile).filter(
                SurveyFile.survey_id == task.survey_id,
                SurveyFile.ingestion_status == "VALIDATED",
                SurveyFile.file_type.in_(["RAW_IMAGE", "RAW_ZIP"]),
            ).all()

        if not source_files:
            error_msg = f"No validated raw drone image files found for survey {survey.survey_code}."
            task.status = "FAILED"
            task.error_message = error_msg
            task.completed_at = datetime.utcnow()
            survey.status = "FAILED"
            db.commit()
            append_task_log(db, task.id, error_msg, "ERROR")
            return

        append_task_log(db, task.id, f"Reading {len(source_files)} source dataset record(s) from storage...")

        for sfile in source_files:
            blob_path = sfile.blob_uri.split(f"{settings.AZURE_CONTAINER_RAW}/")[-1]
            if blob_path.startswith("local://"):
                blob_path = blob_path.replace(f"local://{settings.AZURE_CONTAINER_RAW}/", "")

            try:
                raw_bytes = storage.download_file(settings.AZURE_CONTAINER_RAW, blob_path)
            except Exception as e:
                error_msg = f"Cannot read source file '{sfile.original_filename}' from storage: {str(e)}"
                task.status = "FAILED"
                task.error_message = error_msg
                task.completed_at = datetime.utcnow()
                survey.status = "FAILED"
                db.commit()
                append_task_log(db, task.id, error_msg, "ERROR")
                return

            if sfile.file_type == "RAW_ZIP":
                append_task_log(db, task.id, f"Extracting images from archive: {sfile.original_filename}")
                try:
                    with zipfile.ZipFile(io.BytesIO(raw_bytes)) as z:
                        for zname in z.namelist():
                            if zname.lower().endswith((".jpg", ".jpeg", ".tif", ".tiff")) and not zname.startswith("__MACOSX"):
                                img_data = z.read(zname)
                                staged_images.append((zname, img_data))
                except Exception as e:
                    error_msg = f"Failed to extract zip archive '{sfile.original_filename}': {str(e)}"
                    task.status = "FAILED"
                    task.error_message = error_msg
                    task.completed_at = datetime.utcnow()
                    survey.status = "FAILED"
                    db.commit()
                    append_task_log(db, task.id, error_msg, "ERROR")
                    return
            else:
                staged_images.append((sfile.original_filename, raw_bytes))

        if not staged_images:
            error_msg = "No compatible JPEG/TIFF photos found inside the submitted dataset."
            task.status = "FAILED"
            task.error_message = error_msg
            task.completed_at = datetime.utcnow()
            survey.status = "FAILED"
            db.commit()
            append_task_log(db, task.id, error_msg, "ERROR")
            return

        append_task_log(db, task.id, f"Staged {len(staged_images)} individual photographs for photogrammetric reconstruction.")

        # 3. Check WebODM connectivity
        append_task_log(db, task.id, f"Verifying WebODM cluster connectivity at {webodm.api_url}...")
        cluster_health = webodm.check_cluster_health()
        if not cluster_health["is_connected"]:
            error_msg = f"WebODM photogrammetry cluster is unreachable at {webodm.api_url}. Error: {cluster_health.get('error_message')}"
            task.status = "FAILED"
            task.error_message = error_msg
            task.completed_at = datetime.utcnow()
            survey.status = "FAILED"
            db.commit()
            append_task_log(db, task.id, error_msg, "ERROR")
            return

        # 4. State: UPLOADING & Task Creation
        task.status = "UPLOADING"
        task.progress_percent = 15
        task.current_stage = f"Uploading {len(staged_images)} photos to WebODM cluster"
        db.commit()
        append_task_log(db, task.id, f"Dispatching dataset to WebODM...")

        # Build options
        options = webodm.build_options_payload(
            resolution_preset=task.resolution_preset,
            generate_dsm=task.generate_dsm,
            generate_dtm=task.generate_dtm,
            radiometric_calibration=task.radiometric_calibration,
        )

        task_name = f"AgriDrone_{survey.survey_code}_{str(task.id)[:8]}"

        try:
            webodm_uuid = webodm.create_task(
                task_name=task_name,
                image_files=staged_images,
                options=options,
            )
            task.webodm_task_uuid = webodm_uuid
            task.status = "RUNNING"
            task.progress_percent = 20
            task.current_stage = "Reconstruction in progress on WebODM"
            db.commit()
            append_task_log(db, task.id, f"WebODM task created successfully. Task UUID: {webodm_uuid}")
        except Exception as e:
            error_msg = f"WebODM task submission failed: {str(e)}"
            task.status = "FAILED"
            task.error_message = error_msg
            task.completed_at = datetime.utcnow()
            survey.status = "FAILED"
            db.commit()
            append_task_log(db, task.id, error_msg, "ERROR")
            return

        # 5. Polling Loop
        append_task_log(db, task.id, "Starting live status and log polling loop...")
        logged_line_count = 0
        poll_interval = settings.WEBODM_POLL_INTERVAL_SECONDS
        max_duration_seconds = 14400  # 4 hours
        start_time = time.time()

        while (time.time() - start_time) < max_duration_seconds:
            # Check for cancellation requested from DB
            db.refresh(task)
            if task.status == "CANCEL_REQUESTED":
                append_task_log(db, task.id, "Cancellation requested by user. Aborting WebODM task...", "WARNING")
                try:
                    webodm.cancel_task(task.webodm_task_uuid)
                except Exception as cancel_err:
                    logger.warning("Error cancelling WebODM task %s: %s", task.webodm_task_uuid, str(cancel_err))
                task.status = "CANCELLED"
                task.completed_at = datetime.utcnow()
                task.current_stage = "Cancelled by user"
                survey.status = "DRAFT"
                db.commit()
                append_task_log(db, task.id, "Task successfully cancelled.", "WARNING")
                return

            try:
                status_info = webodm.get_task_status(task.webodm_task_uuid)
            except Exception as poll_err:
                append_task_log(db, task.id, f"Polling warning: {str(poll_err)}", "WARNING")
                time.sleep(poll_interval)
                continue

            current_status = status_info["status"]
            progress = status_info.get("progress_percent", task.progress_percent)
            stage = status_info.get("current_stage", task.current_stage)

            task.progress_percent = max(task.progress_percent, progress)
            task.current_stage = stage
            db.commit()

            # Fetch console output lines
            try:
                new_logs = webodm.get_task_logs(task.webodm_task_uuid, line_offset=logged_line_count)
                if new_logs:
                    for line in new_logs:
                        append_task_log(db, task.id, line)
                    logged_line_count += len(new_logs)
            except Exception:
                pass

            if current_status == "COMPLETED":
                append_task_log(db, task.id, "WebODM reporting photogrammetry task COMPLETED. Finalizing artifacts...")
                break
            elif current_status in ("FAILED", "CANCELLED"):
                error_msg = status_info.get("error_message") or f"WebODM task ended with status {current_status}"
                task.status = current_status
                task.error_message = error_msg
                task.completed_at = datetime.utcnow()
                survey.status = "FAILED" if current_status == "FAILED" else "DRAFT"
                db.commit()
                append_task_log(db, task.id, error_msg, "ERROR" if current_status == "FAILED" else "WARNING")
                return

            time.sleep(poll_interval)

        # 6. State: FINALIZING & Output Discovery
        task.status = "FINALIZING"
        task.current_stage = "Downloading & registering output GeoTIFF rasters"
        db.commit()

        # Download Orthophoto
        try:
            append_task_log(db, task.id, "Downloading orthophoto from WebODM...")
            ortho_bytes = webodm.download_artifact(task.webodm_task_uuid, "orthophoto.tif")
            ortho_blob_path = f"{survey.id}/orthophoto_{task.id}.tif"
            upload_res = storage.upload_file(
                io.BytesIO(ortho_bytes),
                container=settings.AZURE_CONTAINER_ORTHO,
                blob_path=ortho_blob_path,
                content_type="image/tiff",
            )
            append_task_log(db, task.id, f"Orthophoto stored in {upload_res['blob_uri']}")

            # Inspect GeoTIFF metadata
            _, tiff_meta = validator._inspect_tiff(ortho_bytes)
            band_count = tiff_meta.get("bands", 3)
            crs_epsg = tiff_meta.get("crs_epsg", "EPSG:4326")
            resolution_cm = float(task.resolution_preset == "HIGH_RES" and 2.5 or 5.0)

            ortho_product = MapProduct(
                survey_id=task.survey_id,
                source_task_id=task.id,
                product_type="ORTHOPHOTO",
                blob_uri=upload_res["blob_uri"],
                is_cog=True,
                band_count=band_count,
                crs_epsg=crs_epsg,
                resolution_cm_px=resolution_cm,
                is_published=False,
            )
            db.add(ortho_product)
            db.commit()
            append_task_log(db, task.id, f"Registered MapProduct ORTHOPHOTO (ID: {ortho_product.id})")
        except Exception as e:
            logger.warning("Could not download orthophoto.tif: %s", str(e))
            append_task_log(db, task.id, f"Note: orthophoto download encountered: {str(e)}", "WARNING")

        # Download DSM if requested
        if task.generate_dsm:
            try:
                append_task_log(db, task.id, "Downloading Digital Surface Model (DSM) from WebODM...")
                dsm_bytes = webodm.download_artifact(task.webodm_task_uuid, "dsm.tif")
                dsm_blob_path = f"{survey.id}/dsm_{task.id}.tif"
                upload_res = storage.upload_file(
                    io.BytesIO(dsm_bytes),
                    container=settings.AZURE_CONTAINER_ORTHO,
                    blob_path=dsm_blob_path,
                    content_type="image/tiff",
                )
                dsm_product = MapProduct(
                    survey_id=task.survey_id,
                    source_task_id=task.id,
                    product_type="DSM",
                    blob_uri=upload_res["blob_uri"],
                    is_cog=True,
                    band_count=1,
                    crs_epsg="EPSG:4326",
                    resolution_cm_px=5.0,
                    is_published=False,
                )
                db.add(dsm_product)
                db.commit()
                append_task_log(db, task.id, f"Registered MapProduct DSM (ID: {dsm_product.id})")
            except Exception as e:
                logger.warning("Could not download dsm.tif: %s", str(e))
                append_task_log(db, task.id, f"Note: DSM download not available: {str(e)}", "WARNING")

        # Download DTM if requested
        if task.generate_dtm:
            try:
                append_task_log(db, task.id, "Downloading Digital Terrain Model (DTM) from WebODM...")
                dtm_bytes = webodm.download_artifact(task.webodm_task_uuid, "dtm.tif")
                dtm_blob_path = f"{survey.id}/dtm_{task.id}.tif"
                upload_res = storage.upload_file(
                    io.BytesIO(dtm_bytes),
                    container=settings.AZURE_CONTAINER_ORTHO,
                    blob_path=dtm_blob_path,
                    content_type="image/tiff",
                )
                dtm_product = MapProduct(
                    survey_id=task.survey_id,
                    source_task_id=task.id,
                    product_type="DTM",
                    blob_uri=upload_res["blob_uri"],
                    is_cog=True,
                    band_count=1,
                    crs_epsg="EPSG:4326",
                    resolution_cm_px=5.0,
                    is_published=False,
                )
                db.add(dtm_product)
                db.commit()
                append_task_log(db, task.id, f"Registered MapProduct DTM (ID: {dtm_product.id})")
            except Exception as e:
                logger.warning("Could not download dtm.tif: %s", str(e))

        # 7. Mark Task COMPLETED
        task.status = "COMPLETED"
        task.progress_percent = 100
        task.current_stage = "Reconstruction completed & deliverables registered"
        task.completed_at = datetime.utcnow()
        survey.status = "COMPLETED"
        db.commit()
        append_task_log(db, task.id, "Photogrammetry processing workflow successfully completed!")

    except Exception as fatal_e:
        logger.exception("Fatal unhandled exception in photogrammetry task %s: %s", task_id_str, str(fatal_e))
        try:
            task = db.query(PhotogrammetryTask).filter(PhotogrammetryTask.id == task_id).first()
            if task:
                task.status = "FAILED"
                task.error_message = f"Fatal system error: {str(fatal_e)}"
                task.completed_at = datetime.utcnow()
                db.commit()
                append_task_log(db, task.id, f"Fatal error: {str(fatal_e)}", "ERROR")
        except Exception:
            pass
    finally:
        db.close()


@celery_app.task(name="app.tasks.photogrammetry.dispatch_reconstruction", bind=True, max_retries=3)
def dispatch_reconstruction(self, task_id_str: str):
    """Celery worker task for executing photogrammetry pipeline."""
    try:
        execute_photogrammetry_workflow(task_id_str)
    except Exception as exc:
        logger.error("Celery task exception: %s. Retrying...", str(exc))
        raise self.retry(exc=exc, countdown=10)


def trigger_photogrammetry_task(task_id: UUID, use_celery: bool = True) -> bool:
    """Dispatches photogrammetry task via Celery worker, with automatic background thread fallback."""
    task_id_str = str(task_id)
    if use_celery:
        try:
            # Check if redis / celery broker is reachable
            res = dispatch_reconstruction.delay(task_id_str)
            logger.info("Dispatched photogrammetry task %s via Celery (Celery Task ID: %s)", task_id_str, res.id)
            return True
        except Exception as e:
            logger.warning("Celery dispatch unavailable (%s). Falling back to background coordinator thread.", str(e))

    # Thread fallback
    thread = threading.Thread(
        target=execute_photogrammetry_workflow,
        args=(task_id_str,),
        daemon=True,
        name=f"WebODM-Worker-{task_id_str[:8]}",
    )
    thread.start()
    logger.info("Launched photogrammetry task %s in background worker thread.", task_id_str)
    return True
