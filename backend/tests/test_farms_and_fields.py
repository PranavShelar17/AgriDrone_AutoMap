import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

SAMPLE_POLYGON = {
    "type": "Polygon",
    "coordinates": [
        [
            [74.580, 18.150],
            [74.590, 18.150],
            [74.590, 18.160],
            [74.580, 18.160],
            [74.580, 18.150],
        ]
    ],
}


def test_create_and_list_farms():
    # 1. Create Farm with spatial polygon boundary
    payload = {
        "name": "Baramati Research Agronomy Farm",
        "village": "Malegaon",
        "district": "Pune",
        "state": "Maharashtra",
        "boundary_geojson": SAMPLE_POLYGON,
    }
    res = client.post("/api/v1/farms", json=payload)
    assert res.status_code == 201, res.text
    farm_data = res.json()
    farm_id = farm_data["id"]
    assert farm_data["name"] == "Baramati Research Agronomy Farm"
    assert farm_data["village"] == "Malegaon"
    assert farm_data["boundary_geojson"] is not None

    # 2. List farms and verify item is present
    list_res = client.get("/api/v1/farms?search=Baramati")
    assert list_res.status_code == 200
    items = list_res.json()["items"]
    assert any(item["id"] == farm_id for item in items)

    # 3. Create Field attached to this farm
    field_payload = {
        "field_name": "Sugarcane North Block 1",
        "crop_type": "Sugarcane Co 86032",
        "area_hectares": 12.5,
        "boundary_geojson": SAMPLE_POLYGON,
    }
    field_res = client.post(f"/api/v1/farms/{farm_id}/fields", json=field_payload)
    assert field_res.status_code == 201, field_res.text
    field_data = field_res.json()
    assert field_data["field_name"] == "Sugarcane North Block 1"
    assert field_data["area_hectares"] == 12.5

    # 4. Get farm details with attached fields
    detail_res = client.get(f"/api/v1/farms/{farm_id}")
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["fields_count"] == 1
    assert len(detail_data["fields"]) == 1

    # 5. Update farm metadata
    update_res = client.put(f"/api/v1/farms/{farm_id}", json={"name": "Baramati Precision Farm Updated"})
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "Baramati Precision Farm Updated"


def test_reject_field_for_nonexistent_farm():
    random_id = str(uuid.uuid4())
    field_payload = {
        "field_name": "Orphan Field",
        "crop_type": "Corn",
        "area_hectares": 5.0,
    }
    res = client.post(f"/api/v1/farms/{random_id}/fields", json=field_payload)
    assert res.status_code == 404
    assert "does not exist" in res.json()["detail"]


def test_reject_invalid_polygon_geometry():
    invalid_payload = {
        "name": "Bad Polygon Farm",
        "boundary_geojson": {
            "type": "Point",  # Rejected: Must be Polygon
            "coordinates": [74.5, 18.2],
        },
    }
    res = client.post("/api/v1/farms", json=invalid_payload)
    assert res.status_code == 422
    assert "must be a Polygon" in res.json()["detail"]
