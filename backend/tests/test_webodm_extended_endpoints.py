import uuid
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.models.tenant import User
from app.models.farm import Farm, Field
from app.models.survey import Survey
from app.models.task import PhotogrammetryTask
from app.models.product import MapProduct

client = TestClient(app)


def test_options_schema_and_presets_endpoints():
    # 1. Options schema
    res_schema = client.get("/api/v1/photogrammetry/options/schema")
    assert res_schema.status_code == 200
    data_schema = res_schema.json()
    assert isinstance(data_schema, list)
    assert len(data_schema) > 0
    names = [item["name"] for item in data_schema]
    assert "dsm" in names
    assert "dtm" in names
    assert "feature-quality" in names

    # 2. Presets
    res_presets = client.get("/api/v1/photogrammetry/presets")
    assert res_presets.status_code == 200
    data_presets = res_presets.json()
    assert isinstance(data_presets, list)
    assert len(data_presets) >= 4
    preset_codes = [p.get("code") or p.get("name") for p in data_presets]
    assert any("FAST" in c for c in preset_codes)
    assert any("HIGH_RES" in c or "High-Res" in c for c in preset_codes)
    assert any("MULTISPECTRAL" in c or "Multispectral" in c for c in preset_codes)


def test_tiles_and_3d_assets_lifecycle():
    db = SessionLocal()
    user = db.query(User).first()
    farm = Farm(name="Extended Endpoints Farm", owner_id=user.id, district="Pune")
    db.add(farm)
    db.commit()

    field = Field(farm_id=farm.id, field_name="Extended Parcel", area_hectares=5.0)
    db.add(field)
    db.commit()

    survey = Survey(
        field_id=field.id,
        survey_code=f"SRV-EXT-{uuid.uuid4().hex[:6].upper()}",
        flight_date="2026-10-16",
        sensor_type="RGB",
        status="COMPLETED",
    )
    db.add(survey)
    db.commit()

    task = PhotogrammetryTask(
        survey_id=survey.id,
        resolution_preset="HIGH_RES",
        webodm_task_uuid=f"mock-webodm-{uuid.uuid4().hex[:12]}",
        status="COMPLETED",
        progress_percent=100,
    )
    db.add(task)
    db.commit()

    # Add mock products
    prod_mesh = MapProduct(
        survey_id=survey.id,
        source_task_id=task.id,
        product_type="3D_MESH",
        blob_uri=f"local://3d_models/{survey.id}/textured_model.glb",
        is_cog=False,
        band_count=3,
        crs_epsg="EPSG:32643",
        resolution_cm_px=2.5,
    )
    prod_pc = MapProduct(
        survey_id=survey.id,
        source_task_id=task.id,
        product_type="POINT_CLOUD",
        blob_uri=f"local://point_clouds/{survey.id}/point_cloud.laz",
        is_cog=False,
        band_count=1,
        crs_epsg="EPSG:32643",
        resolution_cm_px=2.5,
    )
    db.add_all([prod_mesh, prod_pc])
    db.commit()
    task_id = str(task.id)
    db.close()

    # 3. Test 3D assets endpoint
    res_3d = client.get(f"/api/v1/photogrammetry/tasks/{task_id}/3d-assets")
    assert res_3d.status_code == 200
    data_3d = res_3d.json()
    assert data_3d["task_id"] == task_id
    assert data_3d["textured_mesh"]["available"] is True
    assert data_3d["point_cloud"]["available"] is True
    assert data_3d["textured_mesh"]["download_url"] is not None

    # 4. Test Tiles endpoint with fallback / mock
    with patch("app.services.webodm.WebODMService.get_tile", return_value=None):
        tile_res = client.get(f"/api/v1/photogrammetry/tasks/{task_id}/tiles/orthophoto/10/100/100.png")
        assert tile_res.status_code == 200
        assert tile_res.headers["content-type"] == "image/png"
        assert len(tile_res.content) > 0  # Fallback transparent PNG returned cleanly

    # 5. Test Raster bounds endpoint with fallback
    with patch("app.services.webodm.WebODMService.get_raster_bounds", return_value=None):
        bounds_res = client.get(f"/api/v1/photogrammetry/tasks/{task_id}/tiles/orthophoto/bounds")
        assert bounds_res.status_code == 200
        bounds_data = bounds_res.json()
        assert "bounds" in bounds_data
        assert "task_id" in bounds_data

    # 6. Test Raster metadata endpoint with fallback
    with patch("app.services.webodm.WebODMService.get_raster_metadata", return_value=None):
        meta_res = client.get(f"/api/v1/photogrammetry/tasks/{task_id}/tiles/dsm/metadata")
        assert meta_res.status_code == 200
        meta_data = meta_res.json()
        assert "bands" in meta_data
        assert "task_id" in meta_data

    # 7. Test Download endpoint
    fake_bytes = b"MOCK_ORTHOPHOTO_TIFF_STREAM"
    with patch("app.services.webodm.WebODMService.download_artifact", return_value=fake_bytes):
        dl_res = client.get(f"/api/v1/photogrammetry/tasks/{task_id}/download/orthophoto.tif")
        assert dl_res.status_code == 200
        assert dl_res.content == fake_bytes
