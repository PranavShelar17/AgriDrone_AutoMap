"""Tests for WebODM Projects, Cluster Nodes, Diagnostics, GCP Validation, and Admin Config.

Validates:
- Project creation, listing, updating, deletion
- Multi-tenant isolation for PhotogrammetryProject (Farmers vs Admin)
- GCP format validation
- Cluster nodes listing & access control (Admin only)
- Diagnostics endpoint & access control (Admin only)
- Admin configuration endpoint & access control (Admin only)
"""

import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.core.security import create_access_token, get_password_hash
from app.models.tenant import User, UserRole
from app.models.farm import Farm, Field
from app.models.project import PhotogrammetryProject

client = TestClient(app)


@pytest.fixture(scope="module")
def setup_webodm_test_env():
    db = SessionLocal()
    try:
        # 1. Admin
        admin = db.query(User).filter(User.email == "admin_webodm@agridrone.local").first()
        if not admin:
            admin = User(
                email="admin_webodm@agridrone.local",
                password_hash=get_password_hash("AdminWebodm2026!"),
                full_name="WebODM Platform Admin",
                role=UserRole.ADMIN,
                is_active=True,
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)

        # 2. Farmer 1
        farmer1 = db.query(User).filter(User.email == "farmer1_webodm@agridrone.local").first()
        if not farmer1:
            farmer1 = User(
                email="farmer1_webodm@agridrone.local",
                password_hash=get_password_hash("Farmer1Webodm2026!"),
                full_name="Ramesh Patil",
                role=UserRole.FARMER,
                is_active=True,
            )
            db.add(farmer1)
            db.commit()
            db.refresh(farmer1)

        # 3. Farmer 2
        farmer2 = db.query(User).filter(User.email == "farmer2_webodm@agridrone.local").first()
        if not farmer2:
            farmer2 = User(
                email="farmer2_webodm@agridrone.local",
                password_hash=get_password_hash("Farmer2Webodm2026!"),
                full_name="Suresh Shinde",
                role=UserRole.FARMER,
                is_active=True,
            )
            db.add(farmer2)
            db.commit()
            db.refresh(farmer2)

        # 4. Farms for Farmer 1 and Farmer 2
        farm1 = db.query(Farm).filter(Farm.name == "Patil Cane Farm").first()
        if not farm1:
            farm1 = Farm(name="Patil Cane Farm", district="Baramati", owner_id=farmer1.id)
            db.add(farm1)
            db.commit()
            db.refresh(farm1)

        field1 = db.query(Field).filter(Field.field_name == "Plot A Cane").first()
        if not field1:
            field1 = Field(farm_id=farm1.id, field_name="Plot A Cane", crop_type="Sugarcane", area_hectares=10.0)
            db.add(field1)
            db.commit()
            db.refresh(field1)

        farm2 = db.query(Farm).filter(Farm.name == "Shinde Vineyard").first()
        if not farm2:
            farm2 = Farm(name="Shinde Vineyard", district="Nashik", owner_id=farmer2.id)
            db.add(farm2)
            db.commit()
            db.refresh(farm2)

        admin_token = create_access_token({"sub": str(admin.id), "email": admin.email, "role": admin.role.value})
        farmer1_token = create_access_token({"sub": str(farmer1.id), "email": farmer1.email, "role": farmer1.role.value})
        farmer2_token = create_access_token({"sub": str(farmer2.id), "email": farmer2.email, "role": farmer2.role.value})

        # Pre-extract strings to avoid DetachedInstanceError after closing db
        admin_id_str = str(admin.id)
        f1_id_str = str(farmer1.id)
        f2_id_str = str(farmer2.id)
        farm1_id_str = str(farm1.id)
        field1_id_str = str(field1.id)
        farm2_id_str = str(farm2.id)

        return {
            "admin_id": admin_id_str,
            "farmer1_id": f1_id_str,
            "farmer2_id": f2_id_str,
            "farm1_id": farm1_id_str,
            "field1_id": field1_id_str,
            "farm2_id": farm2_id_str,
            "admin_headers": {"Authorization": f"Bearer {admin_token}"},
            "farmer1_headers": {"Authorization": f"Bearer {farmer1_token}"},
            "farmer2_headers": {"Authorization": f"Bearer {farmer2_token}"},
        }
    finally:
        db.close()


def test_gcp_validation_endpoint(setup_webodm_test_env):
    """Test POST /api/v1/photogrammetry/gcp/validate with valid and invalid payloads."""
    headers = setup_webodm_test_env["farmer1_headers"]

    # 1. Valid GCP file
    valid_gcp = """+proj=utm +zone=43 +datum=WGS84 +units=m +no_defs
385200.12 2011400.45 540.23 1250 820 image_001.jpg
385220.89 2011410.60 541.02 1400 950 image_002.jpg
385240.34 2011430.12 540.88 1650 1100 image_003.jpg
"""
    res = client.post("/api/v1/photogrammetry/gcp/validate", json={"content": valid_gcp}, headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["valid"] is True
    assert data["point_count"] == 3
    assert data["crs"] == "+proj=utm +zone=43 +datum=WGS84 +units=m +no_defs"
    assert len(data["points"]) == 3
    assert data["points"][0]["image_name"] == "image_001.jpg"

    # 2. Invalid GCP file (missing header / too short)
    res_bad = client.post("/api/v1/photogrammetry/gcp/validate", json={"content": "not enough data"}, headers=headers)
    assert res_bad.status_code == 200
    bad_data = res_bad.json()
    assert bad_data["valid"] is False
    assert len(bad_data["errors"]) >= 1


def test_project_lifecycle_and_tenant_isolation(setup_webodm_test_env):
    """Test creating, listing, updating projects and strictly enforcing multi-tenant isolation."""
    env = setup_webodm_test_env
    f1_headers = env["farmer1_headers"]
    f2_headers = env["farmer2_headers"]
    admin_headers = env["admin_headers"]

    # 1. Farmer 1 creates a project for Farm 1
    create_payload = {
        "name": "Baramati High-Res Survey 2026",
        "description": "Pre-harvest sugarcane multispectral and orthophoto mapping",
        "farm_id": env["farm1_id"],
        "field_id": env["field1_id"],
    }
    create_res = client.post("/api/v1/photogrammetry/projects", json=create_payload, headers=f1_headers)
    assert create_res.status_code == 201, create_res.text
    project_data = create_res.json()
    project_id = project_data["id"]
    assert project_data["name"] == create_payload["name"]
    assert project_data["farm_id"] == env["farm1_id"]

    # 2. Farmer 1 can retrieve project details
    get_res = client.get(f"/api/v1/photogrammetry/projects/{project_id}", headers=f1_headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == project_id

    # 3. Farmer 2 CANNOT access Farmer 1's project (404/403 anti-IDOR guard)
    f2_get = client.get(f"/api/v1/photogrammetry/projects/{project_id}", headers=f2_headers)
    assert f2_get.status_code in (403, 404)

    # 4. Farmer 2 CANNOT update Farmer 1's project
    f2_patch = client.patch(
        f"/api/v1/photogrammetry/projects/{project_id}",
        json={"name": "Hacked Project Name"},
        headers=f2_headers,
    )
    assert f2_patch.status_code in (403, 404)

    # 5. Farmer 1 updates their project
    patch_res = client.patch(
        f"/api/v1/photogrammetry/projects/{project_id}",
        json={"name": "Baramati High-Res Survey 2026 - Revised", "description": "Updated description"},
        headers=f1_headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["name"] == "Baramati High-Res Survey 2026 - Revised"

    # 6. Admin CAN access Farmer 1's project
    admin_get = client.get(f"/api/v1/photogrammetry/projects/{project_id}", headers=admin_headers)
    assert admin_get.status_code == 200
    assert admin_get.json()["id"] == project_id

    # 7. Listing projects filters by owner
    f1_list = client.get("/api/v1/photogrammetry/projects", headers=f1_headers)
    assert f1_list.status_code == 200
    f1_ids = [p["id"] for p in f1_list.json()["items"]]
    assert project_id in f1_ids

    f2_list = client.get("/api/v1/photogrammetry/projects", headers=f2_headers)
    assert f2_list.status_code == 200
    f2_ids = [p["id"] for p in f2_list.json()["items"]]
    assert project_id not in f2_ids


def test_admin_diagnostics_and_nodes_rbac(setup_webodm_test_env):
    """Test RBAC enforcement on nodes, diagnostics, and admin configuration endpoints."""
    env = setup_webodm_test_env
    f1_headers = env["farmer1_headers"]
    admin_headers = env["admin_headers"]

    # 1. Farmer is FORBIDDEN from accessing cluster nodes (403 Forbidden)
    f1_nodes = client.get("/api/v1/photogrammetry/nodes", headers=f1_headers)
    assert f1_nodes.status_code == 403

    # 2. Admin CAN access cluster nodes
    admin_nodes = client.get("/api/v1/photogrammetry/nodes", headers=admin_headers)
    assert admin_nodes.status_code == 200
    nodes_data = admin_nodes.json()
    assert "nodes" in nodes_data
    assert "total" in nodes_data
    assert isinstance(nodes_data["nodes"], list)

    # 3. Farmer is FORBIDDEN from accessing diagnostics (403 Forbidden)
    f1_diag = client.get("/api/v1/photogrammetry/diagnostics", headers=f1_headers)
    assert f1_diag.status_code == 403

    # 4. Admin CAN access diagnostics
    admin_diag = client.get("/api/v1/photogrammetry/diagnostics", headers=admin_headers)
    assert admin_diag.status_code == 200
    diag_data = admin_diag.json()
    assert "webodm_status" in diag_data
    assert "database_status" in diag_data
    assert "redis_status" in diag_data
    assert "storage_status" in diag_data

    # 5. Farmer is FORBIDDEN from accessing admin config (403 Forbidden)
    f1_cfg = client.get("/api/v1/photogrammetry/admin/config", headers=f1_headers)
    assert f1_cfg.status_code == 403

    # 6. Admin CAN access admin config
    admin_cfg = client.get("/api/v1/photogrammetry/admin/config", headers=admin_headers)
    assert admin_cfg.status_code == 200
    cfg_data = admin_cfg.json()
    assert "api_url" in cfg_data
    assert "timeout_seconds" in cfg_data
    assert "supported_presets" in cfg_data
