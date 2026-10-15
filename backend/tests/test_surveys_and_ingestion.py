import io
import uuid
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app

client = TestClient(app)


def _create_jpeg_bytes() -> bytes:
    img = Image.new("RGB", (120, 90), color=(50, 150, 50))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_survey_creation_and_file_ingestion():
    # 1. Setup Farm & Field
    farm_res = client.post("/api/v1/farms", json={"name": "Ingestion Test Farm", "district": "Pune"})
    assert farm_res.status_code == 201
    farm_id = farm_res.json()["id"]

    field_res = client.post(
        f"/api/v1/farms/{farm_id}/fields",
        json={"field_name": "Ingestion Field Alpha", "crop_type": "Soybean", "area_hectares": 8.5},
    )
    assert field_res.status_code == 201
    field_id = field_res.json()["id"]

    # 2. Create Survey linked to the field
    survey_payload = {
        "field_id": field_id,
        "flight_date": "2026-10-14",
        "drone_model": "DJI Mavic 3 Enterprise",
        "sensor_type": "RGB",
        "flight_altitude_m": 75.0,
    }
    survey_res = client.post("/api/v1/surveys", json=survey_payload)
    assert survey_res.status_code == 201, survey_res.text
    survey_data = survey_res.json()
    survey_id = survey_data["id"]
    assert survey_data["status"] == "DRAFT"
    assert survey_data["survey_code"].startswith("SRV-2026-")

    # 3. Upload a valid JPEG raw photograph
    jpeg_bytes = _create_jpeg_bytes()
    upload_res = client.post(
        f"/api/v1/ingestion/upload/{survey_id}",
        files={"file": ("DJI_0001.JPG", jpeg_bytes, "image/jpeg")},
        data={"workflow_mode": "raw_photos"},
    )
    assert upload_res.status_code == 201, upload_res.text
    upload_data = upload_res.json()
    assert upload_data["original_filename"] == "DJI_0001.JPG"
    assert upload_data["ingestion_status"] == "VALIDATED"
    assert upload_data["workflow_route"] == "WEBODM_PHOTOGRAMMETRY"
    assert upload_data["file_type"] == "RAW_IMAGE"

    # Verify survey status transitioned from DRAFT to INGESTED
    survey_check = client.get(f"/api/v1/surveys/{survey_id}")
    assert survey_check.status_code == 200
    assert survey_check.json()["status"] == "INGESTED"
    assert survey_check.json()["files_count"] == 1

    # 4. Upload an invalid disguised file
    fake_data = b"FAKE_BINARY_NOT_AN_IMAGE_CONTENT"
    bad_upload_res = client.post(
        f"/api/v1/ingestion/upload/{survey_id}",
        files={"file": ("corrupt.jpg", fake_data, "image/jpeg")},
        data={"workflow_mode": "raw_photos"},
    )
    assert bad_upload_res.status_code == 201
    bad_data = bad_upload_res.json()
    assert bad_data["ingestion_status"] == "REJECTED"
    assert len(bad_data["validation_errors"]) > 0

    # 5. List all files for the survey
    files_list_res = client.get(f"/api/v1/ingestion/surveys/{survey_id}/files")
    assert files_list_res.status_code == 200
    files_list = files_list_res.json()
    assert files_list["total_files"] == 2
    assert files_list["validated_count"] == 1
    assert files_list["rejected_count"] == 1

    # 6. Verify Dashboard stats reflect real database counts
    dashboard_res = client.get("/api/v1/dashboard/stats")
    assert dashboard_res.status_code == 200
    stats = dashboard_res.json()
    assert stats["total_farms"] >= 1
    assert stats["total_fields"] >= 1
    assert stats["total_surveys"] >= 1
    assert stats["total_datasets"] >= 2
    assert stats["datasets_validated"] >= 1
    assert stats["datasets_rejected"] >= 1
    assert len(stats["recent_surveys"]) >= 1
    assert len(stats["recent_uploads"]) >= 1
    assert len(stats["recent_failures"]) >= 1


def test_reject_survey_for_nonexistent_field():
    random_id = str(uuid.uuid4())
    res = client.post(
        "/api/v1/surveys",
        json={"field_id": random_id, "flight_date": "2026-10-14"},
    )
    assert res.status_code == 404
    assert "does not exist" in res.json()["detail"]


def test_reject_upload_for_nonexistent_survey():
    random_id = str(uuid.uuid4())
    res = client.post(
        f"/api/v1/ingestion/upload/{random_id}",
        files={"file": ("test.jpg", b"dummy", "image/jpeg")},
    )
    assert res.status_code == 404
