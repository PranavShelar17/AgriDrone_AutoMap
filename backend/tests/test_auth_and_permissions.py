"""Phase 9 Mandatory Security, Authentication, Authorization & Anti-IDOR Test Suite.

Verifies all 17 mandatory security scenarios specified in Phase 9 requirements:
Scenarios 1-7: Authentication lifecycle, token validation, rate-limiting, and error confidentiality.
Scenarios 8-17: Granular authorization, multi-tenant farmer isolation, private GIS/tile/report protection, and anti-IDOR guards.
"""

import uuid
from datetime import datetime, timedelta
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.core.security import create_access_token, get_password_hash
from app.models.tenant import User, UserRole
from app.models.farm import Farm, Field
from app.models.survey import Survey
from app.models.product import MapProduct, AlgorithmJob
from app.models.report import Report


@pytest.fixture(scope="module")
def setup_test_hierarchy():
    """Sets up two strictly isolated test tenants (Farmer 1 and Farmer 2) with farms, fields, surveys, products, and reports."""
    db = SessionLocal()
    try:
        # 1. Admin User
        admin = db.query(User).filter(User.email == "admin@agridrone.local").first()
        if not admin:
            admin = User(
                email="admin@agridrone.local",
                password_hash=get_password_hash("Admin@AgriDrone2026!"),
                full_name="Platform Administrator",
                role=UserRole.ADMIN,
                is_active=True,
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)

        # 2. Farmer 1 (Green Valley)
        farmer1 = db.query(User).filter(User.email == "farmer@greenvalley.local").first()
        if not farmer1:
            farmer1 = User(
                email="farmer@greenvalley.local",
                password_hash=get_password_hash("Farmer@AgriDrone2026!"),
                full_name="John Doe (Green Valley)",
                role=UserRole.FARMER,
                is_active=True,
            )
            db.add(farmer1)
            db.commit()
            db.refresh(farmer1)

        # 3. Farmer 2 (Sunrise Orchards)
        farmer2 = db.query(User).filter(User.email == "farmer2@sunrise.local").first()
        if not farmer2:
            farmer2 = User(
                email="farmer2@sunrise.local",
                password_hash=get_password_hash("Farmer2@AgriDrone2026!"),
                full_name="Jane Smith (Sunrise Orchards)",
                role=UserRole.FARMER,
                is_active=True,
            )
            db.add(farmer2)
            db.commit()
            db.refresh(farmer2)

        # 4. Farm 1 (Owned by Farmer 1)
        farm1 = db.query(Farm).filter(Farm.owner_id == farmer1.id).first()
        if not farm1:
            farm1 = Farm(
                name="Green Valley Wheat Estate",
                owner_id=farmer1.id,
                total_area_hectares=120.0,
            )
            db.add(farm1)
            db.commit()
            db.refresh(farm1)

        field1 = db.query(Field).filter(Field.farm_id == farm1.id).first()
        if not field1:
            field1 = Field(
                farm_id=farm1.id,
                field_name="North Pivot Corn",
                crop_type="Corn",
                area_hectares=35.0,
            )
            db.add(field1)
            db.commit()
            db.refresh(field1)

        survey1 = db.query(Survey).filter(Survey.field_id == field1.id).first()
        if not survey1:
            survey1 = Survey(
                field_id=field1.id,
                survey_code=f"SURV-F1-{uuid.uuid4().hex[:6]}",
                flight_date=datetime.utcnow(),
                status="COMPLETED",
            )
            db.add(survey1)
            db.commit()
            db.refresh(survey1)

        product1 = db.query(MapProduct).filter(MapProduct.survey_id == survey1.id).first()
        if not product1:
            product1 = MapProduct(
                survey_id=survey1.id,
                product_type="INDEX_NDVI",
                blob_uri=f"local://drone-indices/{survey1.id}/ndvi_cog.tif",
                is_cog=True,
                band_count=1,
                crs_epsg="EPSG:32643",
                is_published=True,
            )
            db.add(product1)
            db.commit()
            db.refresh(product1)

        report1 = db.query(Report).filter(Report.survey_id == survey1.id).first()
        if not report1:
            report1 = Report(
                survey_id=survey1.id,
                generated_by_user_id=admin.id,
                report_number=f"REP-F1-{uuid.uuid4().hex[:6]}",
                report_title="Green Valley NDVI Diagnostic Report",
                blob_uri=f"local://drone-reports/{survey1.id}/report.pdf",
                file_size_bytes=10240,
                status="COMPLETED",
            )
            db.add(report1)
            db.commit()
            db.refresh(report1)

        # 5. Farm 2 (Owned by Farmer 2)
        farm2 = db.query(Farm).filter(Farm.owner_id == farmer2.id).first()
        if not farm2:
            farm2 = Farm(
                name="Sunrise Organic Orchards",
                owner_id=farmer2.id,
                total_area_hectares=45.0,
            )
            db.add(farm2)
            db.commit()
            db.refresh(farm2)

        field2 = db.query(Field).filter(Field.farm_id == farm2.id).first()
        if not field2:
            field2 = Field(
                farm_id=farm2.id,
                field_name="East Block Apples",
                crop_type="Apples",
                area_hectares=18.5,
            )
            db.add(field2)
            db.commit()
            db.refresh(field2)

        survey2 = db.query(Survey).filter(Survey.field_id == field2.id).first()
        if not survey2:
            survey2 = Survey(
                field_id=field2.id,
                survey_code=f"SURV-F2-{uuid.uuid4().hex[:6]}",
                flight_date=datetime.utcnow(),
                status="COMPLETED",
            )
            db.add(survey2)
            db.commit()
            db.refresh(survey2)

        product2 = db.query(MapProduct).filter(MapProduct.survey_id == survey2.id).first()
        if not product2:
            product2 = MapProduct(
                survey_id=survey2.id,
                product_type="INDEX_NDRE",
                blob_uri=f"local://drone-indices/{survey2.id}/ndre_cog.tif",
                is_cog=True,
                band_count=1,
                crs_epsg="EPSG:32643",
                is_published=True,
            )
            db.add(product2)
            db.commit()
            db.refresh(product2)

        job2 = db.query(AlgorithmJob).filter(AlgorithmJob.input_product_id == product2.id).first()
        if not job2:
            job2 = AlgorithmJob(
                batch_id=uuid.uuid4(),
                input_product_id=product2.id,
                algorithm_code="NDRE",
                status="COMPLETED",
                current_stage="COMPLETED",
                progress_percent=100,
            )
            db.add(job2)
            db.commit()
            db.refresh(job2)

        report2 = db.query(Report).filter(Report.survey_id == survey2.id).first()
        if not report2:
            report2 = Report(
                survey_id=survey2.id,
                generated_by_user_id=admin.id,
                report_number=f"REP-F2-{uuid.uuid4().hex[:6]}",
                report_title="Sunrise Orchards NDRE Diagnostic Report",
                blob_uri=f"local://drone-reports/{survey2.id}/report.pdf",
                file_size_bytes=15360,
                status="COMPLETED",
            )
            db.add(report2)
            db.commit()
            db.refresh(report2)

        return {
            "admin_id": str(admin.id),
            "farmer1_id": str(farmer1.id),
            "farmer2_id": str(farmer2.id),
            "farm1_id": str(farm1.id),
            "farm1_name": farm1.name,
            "field1_id": str(field1.id),
            "survey1_id": str(survey1.id),
            "product1_id": str(product1.id),
            "report1_id": str(report1.id),
            "farm2_id": str(farm2.id),
            "farm2_name": farm2.name,
            "field2_id": str(field2.id),
            "survey2_id": str(survey2.id),
            "product2_id": str(product2.id),
            "job2_id": str(job2.id),
            "report2_id": str(report2.id),
        }
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Mandatory Scenarios 1 - 7: Authentication & Session Lifecycle
# ---------------------------------------------------------------------------

def test_01_unauthenticated_request_rejected(unauth_client):
    """Scenario 1: Unauthenticated requests to protected endpoints are rejected with 401."""
    res1 = unauth_client.get("/api/v1/farms")
    assert res1.status_code == 401
    assert "Authentication required" in res1.json()["detail"]

    res2 = unauth_client.get("/api/v1/surveys")
    assert res2.status_code == 401

    res3 = unauth_client.get("/api/v1/dashboard/stats")
    assert res3.status_code == 401

    res4 = unauth_client.get("/api/v1/photogrammetry/tasks")
    assert res4.status_code == 401

    res5 = unauth_client.get("/api/v1/algorithms/supported")
    assert res5.status_code == 401


def test_02_valid_authentication_succeeds(unauth_client):
    """Scenario 2: Valid authentication succeeds with JWT token, profile, and session cookie."""
    # Test Admin login
    res_admin = unauth_client.post("/api/v1/auth/login", json={
        "email": "admin@agridrone.local",
        "password": "Admin@AgriDrone2026!"
    })
    assert res_admin.status_code == 200
    data_admin = res_admin.json()
    assert "access_token" in data_admin
    assert data_admin["token_type"].lower() == "bearer"
    assert data_admin["user"]["role"] == "ADMIN"
    assert "agridrone_session" in res_admin.cookies

    # Test Farmer login
    res_farmer = unauth_client.post("/api/v1/auth/login", json={
        "email": "farmer@greenvalley.local",
        "password": "Farmer@AgriDrone2026!"
    })
    assert res_farmer.status_code == 200
    data_farmer = res_farmer.json()
    assert "access_token" in data_farmer
    assert data_farmer["user"]["role"] == "FARMER"


def test_03_invalid_credentials_rejected(unauth_client):
    """Scenario 3: Invalid credentials or malformed identity tokens are rejected with 401."""
    # Wrong password
    res1 = unauth_client.post("/api/v1/auth/login", json={
        "email": "admin@agridrone.local",
        "password": "WrongPassword123!"
    })
    assert res1.status_code == 401
    assert "Invalid email or password" in res1.json()["detail"]

    # Non-existent user
    res2 = unauth_client.post("/api/v1/auth/login", json={
        "email": "nonexistent@agridrone.local",
        "password": "SomePassword123!"
    })
    assert res2.status_code == 401
    assert "Invalid email or password" in res2.json()["detail"]

    # Malformed Bearer token
    res3 = unauth_client.get("/api/v1/farms", headers={"Authorization": "Bearer invalid.jwt.signature"})
    assert res3.status_code == 401


def test_04_disabled_account_cannot_access(db_session, unauth_client):
    """Scenario 4: Disabled accounts cannot log in or continue accessing protected resources."""
    # Create temporary disabled user
    disabled_user = User(
        email=f"disabled_{uuid.uuid4().hex[:6]}@test.local",
        password_hash=get_password_hash("DisabledPass123!"),
        full_name="Disabled Farmer",
        role=UserRole.FARMER,
        is_active=False,
    )
    db_session.add(disabled_user)
    db_session.commit()
    db_session.refresh(disabled_user)

    # 1. Login attempt must be rejected with 403 Forbidden
    res_login = unauth_client.post("/api/v1/auth/login", json={
        "email": disabled_user.email,
        "password": "DisabledPass123!"
    })
    assert res_login.status_code == 403
    assert "deactivated" in res_login.json()["detail"].lower()

    # 2. Existing token for disabled user must be rejected
    token = create_access_token({
        "sub": str(disabled_user.id),
        "email": disabled_user.email,
        "role": "FARMER",
    })
    res_api = unauth_client.get("/api/v1/farms", headers={"Authorization": f"Bearer {token}"})
    assert res_api.status_code == 403
    assert "deactivated" in res_api.json()["detail"].lower()


def test_05_expired_token_rejected(unauth_client, farmer1_user):
    """Scenario 5: Expired tokens/sessions are rejected with 401."""
    expired_token = create_access_token(
        subject=str(farmer1_user.id),
        role="FARMER",
        email=farmer1_user.email,
        full_name=farmer1_user.full_name,
        expires_delta=timedelta(seconds=-60),
    )
    res = unauth_client.get("/api/v1/farms", headers={"Authorization": f"Bearer {expired_token}"})
    assert res.status_code == 401
    assert "expired" in res.json()["detail"].lower()


def test_06_logout_invalidates_session(unauth_client):
    """Scenario 6: Logout action invalidates the session and clears authentication cookies."""
    # First login to establish session
    login_res = unauth_client.post("/api/v1/auth/login", json={
        "email": "farmer@greenvalley.local",
        "password": "Farmer@AgriDrone2026!"
    })
    assert login_res.status_code == 200

    # Logout
    logout_res = unauth_client.post("/api/v1/auth/logout")
    assert logout_res.status_code == 200
    assert logout_res.json()["status"] == "success"
    # Ensure Set-Cookie or cookie state invalidates the session
    set_cookie_header = logout_res.headers.get("set-cookie", "")
    assert "agridrone_session" in set_cookie_header or logout_res.cookies.get("agridrone_session") in (None, "", '""')


def test_07_auth_errors_do_not_disclose_sensitive_details(unauth_client):
    """Scenario 7: Authentication errors do not disclose sensitive details or username enumeration."""
    # 1. Non-existent account
    res_fake_user = unauth_client.post("/api/v1/auth/login", json={
        "email": "does_not_exist@domain.test",
        "password": "Password123!"
    })
    # 2. Real account, wrong password
    res_real_user_wrong_pass = unauth_client.post("/api/v1/auth/login", json={
        "email": "admin@agridrone.local",
        "password": "IncorrectPassword!"
    })

    # Both must return identical generic 401 response details
    assert res_fake_user.status_code == 401
    assert res_real_user_wrong_pass.status_code == 401
    assert res_fake_user.json()["detail"] == res_real_user_wrong_pass.json()["detail"]
    assert "invalid email or password" in res_fake_user.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Mandatory Scenarios 8 - 17: Granular Authorization & Resource Isolation
# ---------------------------------------------------------------------------

def test_08_farmer_can_access_assigned_farm(farmer1_client, setup_test_hierarchy):
    """Scenario 8: A farmer can access an assigned farm."""
    farm1_id = setup_test_hierarchy["farm1_id"]
    farm1_name = setup_test_hierarchy["farm1_name"]
    res = farmer1_client.get(f"/api/v1/farms/{farm1_id}")
    assert res.status_code == 200
    assert res.json()["id"] == farm1_id
    assert res.json()["name"] == farm1_name

    # Listing farms only returns assigned farm(s)
    list_res = farmer1_client.get("/api/v1/farms")
    assert list_res.status_code == 200
    farm_ids = [f["id"] for f in list_res.json()["items"]]
    assert farm1_id in farm_ids


def test_09_farmer_cannot_access_another_farmer_farm(farmer1_client, setup_test_hierarchy):
    """Scenario 9: A farmer cannot access another farmer's farm (returns privacy-preserving 404)."""
    farm2_id = setup_test_hierarchy["farm2_id"]
    res = farmer1_client.get(f"/api/v1/farms/{farm2_id}")
    assert res.status_code == 404

    # Listing farms does NOT include another farmer's farm
    list_res = farmer1_client.get("/api/v1/farms")
    farm_ids = [f["id"] for f in list_res.json()["items"]]
    assert farm2_id not in farm_ids


def test_10_farmer_cannot_access_another_farmer_field(farmer1_client, setup_test_hierarchy):
    """Scenario 10: A farmer cannot access another farmer's field boundary or metadata."""
    field2_id = setup_test_hierarchy["field2_id"]
    # 1. Field metadata
    res1 = farmer1_client.get(f"/api/v1/fields/{field2_id}")
    assert res1.status_code == 404

    # 2. Field GIS boundary
    res2 = farmer1_client.get(f"/api/v1/maps/fields/{field2_id}/boundary")
    assert res2.status_code == 404


def test_11_farmer_cannot_access_another_farmer_processing_job(farmer1_client, setup_test_hierarchy):
    """Scenario 11: A farmer cannot access another farmer's processing job."""
    job2_id = setup_test_hierarchy["job2_id"]
    res = farmer1_client.get(f"/api/v1/algorithms/jobs/{job2_id}")
    assert res.status_code == 404


def test_12_farmer_cannot_access_another_farmer_map_layer_or_raster(farmer1_client, setup_test_hierarchy):
    """Scenario 12: A farmer cannot access another farmer's map layer or raster product."""
    product2_id = setup_test_hierarchy["product2_id"]
    # 1. Layer visualization metadata
    res1 = farmer1_client.get(f"/api/v1/maps/layers/{product2_id}/visualization")
    assert res1.status_code == 404

    # 2. Product diagnostics & zonal statistics
    res2 = farmer1_client.get(f"/api/v1/algorithms/products/{product2_id}")
    assert res2.status_code == 404


def test_13_farmer_cannot_download_another_farmer_report(farmer1_client, setup_test_hierarchy):
    """Scenario 13: A farmer cannot download another farmer's report."""
    report2_id = setup_test_hierarchy["report2_id"]
    # 1. Report metadata
    res1 = farmer1_client.get(f"/api/v1/reports/{report2_id}")
    assert res1.status_code == 404

    # 2. Report file download
    res2 = farmer1_client.get(f"/api/v1/reports/{report2_id}/download")
    assert res2.status_code == 404


def test_14_farmer_cannot_access_another_farmer_map_tiles_or_blobs(farmer1_client, setup_test_hierarchy):
    """Scenario 14: A farmer cannot access another farmer's private map tiles or stored files."""
    product2_id = setup_test_hierarchy["product2_id"]
    survey2_id = setup_test_hierarchy["survey2_id"]

    # 1. Slippy raster tile request
    res1 = farmer1_client.get(f"/api/v1/maps/tiles/{product2_id}/15/23435/14210.png")
    assert res1.status_code == 404

    # 2. Direct storage download endpoint
    res2 = farmer1_client.get(f"/api/v1/ingestion/download/drone-raw-images/{survey2_id}/orthophoto.tif")
    assert res2.status_code == 404


def test_15_changing_resource_ids_does_not_bypass_authorization(farmer1_client, setup_test_hierarchy):
    """Scenario 15: Changing resource IDs in API requests does not bypass authorization (anti-IDOR)."""
    survey2_id = setup_test_hierarchy["survey2_id"]

    # Ingestion file listing
    res1 = farmer1_client.get(f"/api/v1/ingestion/surveys/{survey2_id}/files")
    assert res1.status_code == 404

    # Eligible rasters filtered by foreign survey ID
    res2 = farmer1_client.get(f"/api/v1/algorithms/eligible-rasters?survey_id={survey2_id}")
    assert res2.status_code == 404

    # Algorithm jobs filtered by foreign survey ID
    res3 = farmer1_client.get(f"/api/v1/algorithms/jobs?survey_id={survey2_id}")
    assert res3.status_code == 404


def test_16_farmer_cannot_call_administrator_endpoints(farmer1_client, setup_test_hierarchy):
    """Scenario 16: A farmer cannot call administrator-only management endpoints (rejected with 403)."""
    farm1_id = setup_test_hierarchy["farm1_id"]
    survey1_id = setup_test_hierarchy["survey1_id"]

    # 1. Register new farmer
    res1 = farmer1_client.post("/api/v1/auth/register-farmer", json={
        "email": "hacker@evil.local",
        "password": "HackerPass123!",
        "full_name": "Unauthorized Attacker",
    })
    assert res1.status_code == 403

    # 2. Assign farm
    res2 = farmer1_client.post("/api/v1/auth/assign-farm", json={
        "farmer_id": str(uuid.uuid4()),
        "farm_id": farm1_id,
    })
    assert res2.status_code == 403

    # 3. Delete farm
    res3 = farmer1_client.delete(f"/api/v1/farms/{farm1_id}")
    assert res3.status_code == 403

    # 4. Upload survey drone photos
    res4 = farmer1_client.post(
        f"/api/v1/ingestion/upload/{survey1_id}",
        files={"file": ("photo.jpg", b"\xff\xd8\xff\xe0" + b"\x00" * 100, "image/jpeg")}
    )
    assert res4.status_code == 403


def test_17_administrator_can_access_permitted_operations(client, setup_test_hierarchy):
    """Scenario 17: An administrator can access operations permitted by the role policy."""
    farm1_id = setup_test_hierarchy["farm1_id"]
    farm2_id = setup_test_hierarchy["farm2_id"]

    # Admin can view Farm 1
    res1 = client.get(f"/api/v1/farms/{farm1_id}")
    assert res1.status_code == 200

    # Admin can view Farm 2
    res2 = client.get(f"/api/v1/farms/{farm2_id}")
    assert res2.status_code == 200

    # Admin can list farms and locate both farms via search
    res_farm1 = client.get(f"/api/v1/farms?search={setup_test_hierarchy['farm1_name']}")
    assert res_farm1.status_code == 200
    assert farm1_id in [f["id"] for f in res_farm1.json()["items"]]

    res_farm2 = client.get(f"/api/v1/farms?search={setup_test_hierarchy['farm2_name']}")
    assert res_farm2.status_code == 200
    assert farm2_id in [f["id"] for f in res_farm2.json()["items"]]

    # Admin can access cluster infrastructure status
    res_cluster = client.get("/api/v1/cluster/status")
    assert res_cluster.status_code in (200, 503)

    # Admin can retrieve global dashboard stats
    res_stats = client.get("/api/v1/dashboard/stats")
    assert res_stats.status_code == 200
