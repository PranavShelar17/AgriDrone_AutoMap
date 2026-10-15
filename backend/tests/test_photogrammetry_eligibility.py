import io
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app

client = TestClient(app)


def _create_jpeg_bytes() -> bytes:
    img = Image.new("RGB", (100, 100), color=(100, 200, 100))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_photogrammetry_dataset_eligibility_classification():
    # 1. Setup Farm, Field, and Survey
    farm_res = client.post("/api/v1/farms", json={"name": "Eligibility Test Farm", "district": "Nashik"})
    assert farm_res.status_code == 201
    farm_id = farm_res.json()["id"]

    field_res = client.post(
        f"/api/v1/farms/{farm_id}/fields",
        json={"field_name": "Eligibility Parcel", "crop_type": "Grapes", "area_hectares": 4.2},
    )
    assert field_res.status_code == 201
    field_id = field_res.json()["id"]

    survey_res = client.post(
        "/api/v1/surveys",
        json={
            "field_id": field_id,
            "flight_date": "2026-10-14",
            "drone_model": "DJI Matrice 300",
            "sensor_type": "RGB",
        },
    )
    assert survey_res.status_code == 201
    survey_id = survey_res.json()["id"]

    # 2. Upload Valid RAW JPEG Photo
    valid_bytes = _create_jpeg_bytes()
    up1 = client.post(
        f"/api/v1/ingestion/upload/{survey_id}",
        files={"file": ("RAW_FLIGHT_01.JPG", valid_bytes, "image/jpeg")},
        data={"workflow_mode": "raw_photos"},
    )
    assert up1.status_code == 201
    assert up1.json()["ingestion_status"] == "VALIDATED"

    # 3. Upload Corrupt / Rejected file
    corrupt_bytes = b"NOT_AN_IMAGE_PAYLOAD"
    up2 = client.post(
        f"/api/v1/ingestion/upload/{survey_id}",
        files={"file": ("corrupt_photo.jpg", corrupt_bytes, "image/jpeg")},
        data={"workflow_mode": "raw_photos"},
    )
    assert up2.status_code == 201
    assert up2.json()["ingestion_status"] == "REJECTED"

    # 4. Upload a GeoTIFF Raster file
    # Synthetic GeoTIFF
    img_tif = Image.new("L", (50, 50), color=128)
    tif_buf = io.BytesIO()
    img_tif.save(tif_buf, format="TIFF")
    up3 = client.post(
        f"/api/v1/ingestion/upload/{survey_id}",
        files={"file": ("stitched_ortho.tif", tif_buf.getvalue(), "image/tiff")},
        data={"workflow_mode": "geotiff"},
    )
    assert up3.status_code == 201

    # 5. Query Eligible Datasets endpoint
    res = client.get(f"/api/v1/photogrammetry/eligible-datasets?survey_id={survey_id}")
    assert res.status_code == 200
    data = res.json()

    assert data["total"] >= 3
    items_by_name = {item["original_filename"]: item for item in data["items"]}

    # Check Valid Raw JPEG
    raw_item = items_by_name["RAW_FLIGHT_01.JPG"]
    assert raw_item["is_eligible"] is True
    assert raw_item["ineligibility_reason"] is None
    assert raw_item["workflow_route"] == "WEBODM_PHOTOGRAMMETRY"

    # Check Rejected Corrupt File
    corrupt_item = items_by_name["corrupt_photo.jpg"]
    assert corrupt_item["is_eligible"] is False
    assert "Rejected" in corrupt_item["ineligibility_reason"]

    # Check GeoTIFF file
    geotiff_item = items_by_name["stitched_ortho.tif"]
    # Even if non-georeferenced in synthetic test, if marked GEOTIFF or workflow DIRECT_ALGORITHM_GIS it's ineligible
    if geotiff_item["file_type"] == "GEOTIFF":
        assert geotiff_item["is_eligible"] is False
        assert "GeoTIFF" in geotiff_item["ineligibility_reason"]
