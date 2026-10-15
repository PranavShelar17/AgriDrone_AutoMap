"""Integration tests for Phase 7 Algorithms & Multi-Map API Endpoints."""

import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.models.tenant import User
from app.models.farm import Farm, Field
from app.models.survey import Survey
from app.models.product import MapProduct, AlgorithmJob


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    """Generates valid JWT auth headers for admin user."""
    db = SessionLocal()
    user = db.query(User).filter(User.email == "admin@agridrone.internal").first()
    db.close()
    if not user:
        return {}
    login_res = client.post("/api/v1/auth/login", data={"username": "admin@agridrone.internal", "password": "AdminPassword123!"})
    if login_res.status_code == 200:
        token = login_res.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    return {}


@pytest.fixture
def api_test_setup():
    db = SessionLocal()
    user = db.query(User).first()
    farm = Farm(owner_id=user.id, name="API Test Farm", state="Haryana", district="Karnal")
    db.add(farm)
    db.flush()

    field = Field(farm_id=farm.id, field_name="Test Field A", area_hectares=5.0, crop_type="PADDY")
    db.add(field)
    db.flush()

    from datetime import date
    survey = Survey(
        field_id=field.id,
        survey_code=f"SRV-API-{uuid.uuid4().hex[:6]}",
        flight_date=date.today(),
        sensor_type="MULTISPECTRAL",
        status="COMPLETED",
    )
    db.add(survey)
    db.flush()

    map_product = MapProduct(
        survey_id=survey.id,
        product_type="ORTHOPHOTO",
        blob_uri="local://orthomosaics/surveys/dummy_ortho.tif",
        is_cog=True,
        band_count=5,
        crs_epsg="EPSG:32643",
        resolution_cm_px=4.5,
        is_published=False,
    )
    db.add(map_product)
    db.commit()
    db.refresh(map_product)

    res = {
        "farm_id": farm.id,
        "field_id": field.id,
        "survey_id": survey.id,
        "product_id": map_product.id,
    }
    db.close()
    return res


def test_get_supported_algorithms(client, auth_headers):
    """Verify GET /api/v1/algorithms/supported returns all 6 vegetation indices."""
    res = client.get("/api/v1/algorithms/supported", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 6

    codes = [a["code"] for a in data]
    assert "NDVI" in codes
    assert "NDRE" in codes
    assert "GNDVI" in codes
    assert "SAVI" in codes
    assert "VARI" in codes
    assert "GLI" in codes

    # Verify SAVI default parameters
    savi = next(a for a in data if a["code"] == "SAVI")
    assert savi["parameters"]["L"] == 0.5


def test_get_eligible_rasters(client, auth_headers, api_test_setup):
    """Verify GET /api/v1/algorithms/eligible-rasters lists available orthophotos."""
    survey_id = api_test_setup["survey_id"]
    res = client.get(f"/api/v1/algorithms/eligible-rasters?survey_id={survey_id}", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1
    assert data["eligible_count"] >= 1

    item = data["items"][0]
    assert item["product_type"] == "ORTHOPHOTO"
    assert item["band_count"] == 5
    assert item["detected_sensor"] == "MULTISPECTRAL"


def test_validate_band_mapping_endpoint(client, auth_headers):
    """Verify POST /api/v1/algorithms/validate-mapping checks compatibility."""
    # Case 1: Valid 5-band mapping
    valid_payload = {
        "band_count": 5,
        "mapping": {"NIR": 5, "RedEdge": 4, "Red": 3, "Green": 2, "Blue": 1},
        "algorithm_codes": ["NDVI", "NDRE", "SAVI"],
    }
    res = client.post("/api/v1/algorithms/validate-mapping", json=valid_payload, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["is_valid"] is True
    assert data["per_algorithm_status"]["NDVI"]["is_valid"] is True
    assert data["per_algorithm_status"]["NDRE"]["is_valid"] is True

    # Case 2: RGB mapping without RedEdge for NDRE
    invalid_payload = {
        "band_count": 3,
        "mapping": {"Red": 1, "Green": 2, "Blue": 3},
        "algorithm_codes": ["NDRE"],
    }
    res_inv = client.post("/api/v1/algorithms/validate-mapping", json=invalid_payload, headers=auth_headers)
    assert res_inv.status_code == 200
    data_inv = res_inv.json()
    assert data_inv["is_valid"] is False
    assert data_inv["per_algorithm_status"]["NDRE"]["is_valid"] is False
    assert "strictly required" in data_inv["per_algorithm_status"]["NDRE"]["error_message"]


def test_submit_algorithm_batch_endpoint(client, auth_headers, api_test_setup):
    """Verify POST /api/v1/algorithms/jobs dispatches multi-algorithm batch with HTTP 202."""
    prod_id = str(api_test_setup["product_id"])

    payload = {
        "source_id": prod_id,
        "source_type": "MAP_PRODUCT",
        "band_mapping": {"NIR": 5, "RedEdge": 4, "Red": 3, "Green": 2, "Blue": 1},
        "algorithms": [
            {"algorithm_code": "NDVI"},
            {"algorithm_code": "NDRE"},
            {"algorithm_code": "SAVI", "parameters": {"L": 0.5}},
        ],
    }

    res = client.post("/api/v1/algorithms/jobs", json=payload, headers=auth_headers)
    assert res.status_code == 202
    data = res.json()

    assert "batch_id" in data
    assert data["total_jobs"] == 3
    assert len(data["jobs"]) == 3
    assert data["status"] == "QUEUED"

    batch_id = data["batch_id"]

    # Verify GET /api/v1/algorithms/batches/{batch_id}
    res_batch = client.get(f"/api/v1/algorithms/batches/{batch_id}", headers=auth_headers)
    assert res_batch.status_code == 200
    batch_data = res_batch.json()
    assert batch_data["batch_id"] == batch_id
    assert batch_data["total_jobs"] == 3


def test_list_and_get_jobs_endpoint(client, auth_headers, api_test_setup):
    """Verify GET /api/v1/algorithms/jobs and GET /api/v1/algorithms/jobs/{job_id}."""
    res_list = client.get("/api/v1/algorithms/jobs?limit=10", headers=auth_headers)
    assert res_list.status_code == 200
    jobs = res_list.json()
    assert isinstance(jobs, list)

    if len(jobs) > 0:
        first_job = jobs[0]
        job_id = first_job["job_id"]
        res_job = client.get(f"/api/v1/algorithms/jobs/{job_id}", headers=auth_headers)
        assert res_job.status_code == 200
        assert res_job.json()["job_id"] == job_id
