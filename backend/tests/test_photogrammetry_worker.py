import io
import uuid
from unittest.mock import patch, MagicMock
from PIL import Image

from app.db.session import SessionLocal
from app.models.tenant import User
from app.models.farm import Farm, Field
from app.models.survey import Survey
from app.models.file import SurveyFile
from app.models.task import PhotogrammetryTask, TaskLog
from app.models.product import MapProduct
from app.services.storage import get_storage_service
from app.tasks.photogrammetry import execute_photogrammetry_workflow


def _create_synthetic_jpeg() -> bytes:
    img = Image.new("RGB", (64, 64), color=(120, 180, 240))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _create_synthetic_tiff() -> bytes:
    img = Image.new("RGB", (64, 64), color=(200, 100, 50))
    buf = io.BytesIO()
    img.save(buf, format="TIFF")
    return buf.getvalue()


def _setup_test_survey_with_photo(db):
    user = db.query(User).first()
    farm = Farm(name="Worker Test Farm", owner_id=user.id, district="Pune")
    db.add(farm)
    db.commit()

    field = Field(farm_id=farm.id, field_name="Worker Plot", area_hectares=5.0)
    db.add(field)
    db.commit()

    survey = Survey(
        field_id=field.id,
        survey_code=f"SRV-WORKER-{uuid.uuid4().hex[:6].upper()}",
        flight_date="2026-10-15",
        sensor_type="RGB",
        status="DRAFT",
    )
    db.add(survey)
    db.commit()

    # Upload raw photo to local storage
    storage = get_storage_service()
    photo_bytes = _create_synthetic_jpeg()
    filename = "IMG_0001.JPG"
    blob_path = f"{survey.id}/{filename}"
    upload_res = storage.upload_file(
        io.BytesIO(photo_bytes),
        container="raw-surveys",
        blob_path=blob_path,
        content_type="image/jpeg",
    )

    sfile = SurveyFile(
        survey_id=survey.id,
        original_filename=filename,
        file_type="RAW_IMAGE",
        file_size_bytes=len(photo_bytes),
        mime_type="image/jpeg",
        blob_uri=upload_res["blob_uri"],
        ingestion_status="VALIDATED",
        validation_metadata={"workflow_route": "WEBODM_PHOTOGRAMMETRY", "metadata": {}},
    )
    db.add(sfile)
    db.commit()

    return farm, field, survey, sfile


def test_worker_handles_cluster_offline():
    """Verifies that if WebODM cluster is offline, task fails fast with clear error and source photos stay intact."""
    db = SessionLocal()
    try:
        farm, field, survey, sfile = _setup_test_survey_with_photo(db)

        task = PhotogrammetryTask(
            survey_id=survey.id,
            source_file_id=sfile.id,
            resolution_preset="HIGH_RES",
            status="SUBMITTED",
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        # WebODM is offline on port 3001 locally
        execute_photogrammetry_workflow(str(task.id))

        db.refresh(task)
        db.refresh(survey)
        assert task.status == "FAILED"
        assert "unreachable" in task.error_message.lower() or "connection" in task.error_message.lower()
        assert task.completed_at is not None
        assert survey.status == "FAILED"

        # Check logs recorded
        logs = db.query(TaskLog).filter(TaskLog.task_id == task.id).all()
        assert len(logs) >= 2
        assert any("error" in l.log_level.lower() for l in logs)

        # Crucial requirement: original source image remains validated and intact
        db.refresh(sfile)
        assert sfile.ingestion_status == "VALIDATED"
        storage = get_storage_service()
        blob_path = f"{survey.id}/IMG_0001.JPG"
        assert storage.file_exists("raw-surveys", blob_path) is True
    finally:
        db.close()


def test_worker_handles_missing_source_file():
    """Verifies that if source file is missing from storage, task fails safely without crashing."""
    db = SessionLocal()
    try:
        farm, field, survey, sfile = _setup_test_survey_with_photo(db)

        # Create file record with non-existent storage path
        missing_file = SurveyFile(
            survey_id=survey.id,
            original_filename="GHOST_FILE.JPG",
            file_type="RAW_IMAGE",
            file_size_bytes=1000,
            mime_type="image/jpeg",
            blob_uri=f"local://raw-surveys/{survey.id}/non_existent_ghost.jpg",
            ingestion_status="VALIDATED",
        )
        db.add(missing_file)
        db.commit()

        task = PhotogrammetryTask(
            survey_id=survey.id,
            source_file_id=missing_file.id,
            resolution_preset="FAST",
            status="SUBMITTED",
        )
        db.add(task)
        db.commit()

        execute_photogrammetry_workflow(str(task.id))

        db.refresh(task)
        assert task.status == "FAILED"
        assert "cannot read source file" in task.error_message.lower() or "not found" in task.error_message.lower()
    finally:
        db.close()


def test_worker_successful_mock_processing_and_artifact_registration():
    """Verifies full execution lifecycle from upload to artifact download & MapProduct registration."""
    db = SessionLocal()
    try:
        farm, field, survey, sfile = _setup_test_survey_with_photo(db)

        task = PhotogrammetryTask(
            survey_id=survey.id,
            source_file_id=sfile.id,
            resolution_preset="HIGH_RES",
            generate_dsm=True,
            generate_dtm=False,
            status="SUBMITTED",
        )
        db.add(task)
        db.commit()

        mock_cluster_health = {
            "cluster_status": "ONLINE",
            "is_connected": True,
            "engine": "NodeODM",
            "available_ram_gb": 16.0,
            "active_nodes": 1,
            "total_nodes": 1,
        }

        mock_task_uuid = f"mock-uuid-{uuid.uuid4().hex[:12]}"
        mock_status_completed = {
            "webodm_task_uuid": mock_task_uuid,
            "status": "COMPLETED",
            "status_code": 40,
            "progress_percent": 100,
            "current_stage": "Task Completed",
            "processing_time_ms": 30000,
            "error_message": None,
            "available_assets": ["orthophoto.tif", "dsm.tif"],
        }

        fake_ortho = _create_synthetic_tiff()

        with patch("app.services.webodm.WebODMService.check_cluster_health", return_value=mock_cluster_health), \
             patch("app.services.webodm.WebODMService.create_task", return_value=mock_task_uuid), \
             patch("app.services.webodm.WebODMService.get_task_status", return_value=mock_status_completed), \
             patch("app.services.webodm.WebODMService.get_task_logs", return_value=["[OpenSfM] Reconstruction complete", "[OpenMVS] Orthophoto generated"]), \
             patch("app.services.webodm.WebODMService.download_artifact", return_value=fake_ortho):

            execute_photogrammetry_workflow(str(task.id))

            db.refresh(task)
            db.refresh(survey)

            assert task.status == "COMPLETED"
            assert task.progress_percent == 100
            assert task.webodm_task_uuid == mock_task_uuid
            assert task.completed_at is not None
            assert survey.status == "COMPLETED"

            # Check registered MapProduct
            products = db.query(MapProduct).filter(MapProduct.source_task_id == task.id).all()
            assert len(products) >= 1
            ortho = next(p for p in products if p.product_type == "ORTHOPHOTO")
            assert ortho.survey_id == survey.id
            assert ortho.is_cog is True
            assert ortho.crs_epsg is not None
            assert "orthomosaics" in ortho.blob_uri
    finally:
        db.close()
