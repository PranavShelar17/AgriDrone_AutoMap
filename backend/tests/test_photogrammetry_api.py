import io
import uuid
from unittest.mock import patch
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.db.session import SessionLocal
from app.models.task import PhotogrammetryTask
from app.models.product import MapProduct
from app.models.farm import Farm, Field
from app.models.survey import Survey

client = TestClient(app)


def _create_jpeg_bytes() -> bytes:
    img = Image.new("RGB", (100, 100), color=(100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_cluster_status_endpoints():
    res1 = client.get("/api/v1/photogrammetry/cluster-status")
    assert res1.status_code == 200
    data1 = res1.json()
    assert "cluster_status" in data1
    assert "is_connected" in data1
    assert data1["cluster_status"] in ("ONLINE", "OFFLINE")

    # Alias /cluster/status
    res2 = client.get("/api/v1/cluster/status")
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["cluster_status"] == data1["cluster_status"]


def test_photogrammetry_task_full_api_lifecycle():
    # 1. Setup Farm, Field, Survey, and Photo
    farm_res = client.post("/api/v1/farms", json={"name": "Photogrammetry Farm", "district": "Baramati"})
    farm_id = farm_res.json()["id"]

    field_res = client.post(
        f"/api/v1/farms/{farm_id}/fields",
        json={"field_name": "Reconstruction Plot", "crop_type": "Sugarcane", "area_hectares": 12.0},
    )
    field_id = field_res.json()["id"]

    survey_res = client.post(
        "/api/v1/surveys",
        json={
            "field_id": field_id,
            "flight_date": "2026-10-14",
            "drone_model": "DJI Phantom 4 RTK",
            "sensor_type": "RGB",
        },
    )
    survey_id = survey_res.json()["id"]

    # Upload raw photo
    up_res = client.post(
        f"/api/v1/ingestion/upload/{survey_id}",
        files={"file": ("SURV_RAW_001.JPG", _create_jpeg_bytes(), "image/jpeg")},
        data={"workflow_mode": "raw_photos"},
    )
    assert up_res.status_code == 201
    file_id = up_res.json()["file_id"]

    # 2. Reject task for non-existent survey
    bad_res = client.post(
        "/api/v1/photogrammetry/tasks",
        json={"survey_id": str(uuid.uuid4()), "resolution_preset": "HIGH_RES"},
    )
    assert bad_res.status_code == 404

    # 3. Create Task with Mocked WebODM execution
    with patch("app.tasks.photogrammetry.trigger_photogrammetry_task", return_value=True):
        task_payload = {
            "survey_id": survey_id,
            "source_file_id": file_id,
            "resolution_preset": "HIGH_RES",
            "custom_resolution_cm": 2.5,
            "generate_dsm": True,
            "generate_dtm": True,
            "radiometric_calibration": False,
            "feature_quality": "high",
            "pc_quality": "medium",
        }
        create_res = client.post("/api/v1/photogrammetry/tasks", json=task_payload)
        assert create_res.status_code == 202, create_res.text
        task_data = create_res.json()

        assert "task_id" in task_data
        task_id = task_data["task_id"]
        assert task_data["survey_id"] == survey_id
        assert task_data["status"] == "SUBMITTED"
        assert task_data["resolution_preset"] == "HIGH_RES"
        assert task_data["generate_dsm"] is True

        # 4. Duplicate concurrency prevention test (409 Conflict)
        conflict_res = client.post("/api/v1/photogrammetry/tasks", json=task_payload)
        assert conflict_res.status_code == 409
        assert "already active" in conflict_res.json()["detail"]

        # 5. Get Task Details
        detail_res = client.get(f"/api/v1/photogrammetry/tasks/{task_id}")
        assert detail_res.status_code == 200
        assert detail_res.json()["task_id"] == task_id
        assert detail_res.json()["source_file_id"] == file_id

        # 6. List Tasks
        list_res = client.get(f"/api/v1/photogrammetry/tasks?survey_id={survey_id}")
        assert list_res.status_code == 200
        assert list_res.json()["total"] >= 1

        # 7. Get Task Logs
        logs_res = client.get(f"/api/v1/photogrammetry/tasks/{task_id}/logs")
        assert logs_res.status_code == 200
        logs_data = logs_res.json()
        assert logs_data["total_lines"] >= 1
        assert any("submitted" in l["message"].lower() for l in logs_data["logs"])

        # 8. Cancel Task
        cancel_res = client.post(f"/api/v1/photogrammetry/tasks/{task_id}/cancel")
        assert cancel_res.status_code == 200
        assert cancel_res.json()["status"] == "CANCELLED"

        # Verify task is now CANCELLED in DB
        check_res = client.get(f"/api/v1/photogrammetry/tasks/{task_id}")
        assert check_res.json()["status"] == "CANCELLED"

        # 9. Retry Cancelled Task
        retry_res = client.post(f"/api/v1/photogrammetry/tasks/{task_id}/retry")
        assert retry_res.status_code == 202
        retried_data = retry_res.json()
        assert retried_data["status"] == "SUBMITTED"
        assert retried_data["retry_count"] == 1

        # 10. Add mock MapProduct and test artifacts listing
        db = SessionLocal()
        mock_product = MapProduct(
            survey_id=uuid.UUID(survey_id),
            source_task_id=uuid.UUID(task_id),
            product_type="ORTHOPHOTO",
            blob_uri=f"local://orthomosaics/{survey_id}/ortho.tif",
            is_cog=True,
            band_count=3,
            crs_epsg="EPSG:32643",
            resolution_cm_px=2.5,
        )
        db.add(mock_product)
        db.commit()
        db.close()

        art_res = client.get(f"/api/v1/photogrammetry/tasks/{task_id}/artifacts")
        assert art_res.status_code == 200
        art_data = art_res.json()
        assert art_data["total"] >= 1
        assert art_data["items"][0]["product_type"] == "ORTHOPHOTO"
        assert art_data["items"][0]["crs_epsg"] == "EPSG:32643"


def test_photogrammetry_api_validation_and_terminal_state_guards():
    # 1. Invalid resolution preset rejected with 422
    res = client.post("/api/v1/photogrammetry/tasks", json={
        "survey_id": str(uuid.uuid4()),
        "resolution_preset": "INVALID_PRESET"
    })
    assert res.status_code == 422

    # 2. Invalid feature quality rejected with 422
    res_fq = client.post("/api/v1/photogrammetry/tasks", json={
        "survey_id": str(uuid.uuid4()),
        "resolution_preset": "HIGH_RES",
        "feature_quality": "extreme_turbo"
    })
    assert res_fq.status_code == 422

    # 3. Setup a completed task to test terminal state guards
    db = SessionLocal()
    from app.models.tenant import User
    user = db.query(User).first()
    farm = Farm(name="Terminal State Farm", owner_id=user.id, district="Kolhapur")
    db.add(farm)
    db.commit()

    field = Field(farm_id=farm.id, field_name="Terminal Plot", area_hectares=3.0)
    db.add(field)
    db.commit()

    survey = Survey(
        field_id=field.id,
        survey_code=f"SRV-TERM-{uuid.uuid4().hex[:6].upper()}",
        flight_date="2026-10-15",
        sensor_type="RGB",
        status="COMPLETED",
    )
    db.add(survey)
    db.commit()

    completed_task = PhotogrammetryTask(
        survey_id=survey.id,
        resolution_preset="HIGH_RES",
        status="COMPLETED",
    )
    db.add(completed_task)
    db.commit()

    # Attempting to cancel a COMPLETED task should return 400
    cancel_res = client.post(f"/api/v1/photogrammetry/tasks/{completed_task.id}/cancel")
    assert cancel_res.status_code == 400
    assert "terminal state" in cancel_res.json()["detail"].lower()

    # Setup a running task
    running_task = PhotogrammetryTask(
        survey_id=survey.id,
        resolution_preset="HIGH_RES",
        status="RUNNING",
    )
    db.add(running_task)
    db.commit()

    # Attempting to retry a RUNNING task should return 400
    retry_res = client.post(f"/api/v1/photogrammetry/tasks/{running_task.id}/retry")
    assert retry_res.status_code == 400
    assert "only failed or cancelled" in retry_res.json()["detail"].lower()

    db.close()

