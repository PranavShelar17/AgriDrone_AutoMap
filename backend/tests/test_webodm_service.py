import pytest
from unittest.mock import patch, MagicMock
import httpx

from app.services.webodm import (
    WebODMService,
    WebODMError,
    WebODMConnectionError,
    WebODMAuthenticationError,
    get_webodm_service,
)


def test_webodm_service_singleton():
    svc1 = get_webodm_service()
    svc2 = get_webodm_service()
    assert svc1 is svc2
    assert svc1.api_url == "http://localhost:3001"


def test_options_payload_builder():
    svc = WebODMService()

    # Default High Res
    opts_high = svc.build_options_payload(resolution_preset="HIGH_RES", generate_dsm=True, generate_dtm=True)
    opts_dict = {o["name"]: o["value"] for o in opts_high}
    assert opts_dict["dsm"] is True
    assert opts_dict["dtm"] is True
    assert opts_dict["orthophoto-resolution"] == 2.5
    assert opts_dict["feature-quality"] == "high"

    # Fast preset
    opts_fast = svc.build_options_payload(resolution_preset="FAST", generate_dsm=True, generate_dtm=False)
    fast_dict = {o["name"]: o["value"] for o in opts_fast}
    assert fast_dict["orthophoto-resolution"] == 5.0
    assert fast_dict["fast-orthophoto"] is True
    assert fast_dict["dtm"] is False

    # Custom resolution
    opts_custom = svc.build_options_payload(
        resolution_preset="CUSTOM",
        custom_resolution_cm=3.2,
        radiometric_calibration=True,
        feature_quality="ultra",
        pc_quality="high",
    )
    cust_dict = {o["name"]: o["value"] for o in opts_custom}
    assert cust_dict["orthophoto-resolution"] == 3.2
    assert cust_dict["radiometric-calibration"] == "camera+sun"
    assert cust_dict["feature-quality"] == "ultra"
    assert cust_dict["pc-quality"] == "high"


def test_cluster_health_when_offline():
    # Test probing an unreachable port
    svc = WebODMService(api_url="http://127.0.0.1:59999", timeout=1)
    health = svc.check_cluster_health()

    assert health["cluster_status"] == "OFFLINE"
    assert health["is_connected"] is False
    assert health["active_nodes"] == 0
    assert "error_message" in health
    assert health["error_message"] is not None


def test_cluster_health_mock_nodeodm_online():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "version": "2.8.5",
        "taskQueueCount": 0,
        "availableMemory": 16 * 1024 * 1024 * 1024,  # 16 GB
    }

    with patch("httpx.Client.get", return_value=mock_resp):
        svc = WebODMService(api_url="http://mock-nodeodm:3000")
        health = svc.check_cluster_health()

        assert health["cluster_status"] == "ONLINE"
        assert health["is_connected"] is True
        assert health["engine"] == "NodeODM"
        assert health["active_nodes"] == 1
        assert health["available_ram_gb"] == 16.0


def test_authenticate_success():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"token": "jwt_test_token_12345"}

    with patch("httpx.Client.post", return_value=mock_resp):
        svc = WebODMService(username="admin", password="password")
        token = svc.authenticate()
        assert token == "jwt_test_token_12345"
        assert svc._get_headers()["Authorization"] == "JWT jwt_test_token_12345"


def test_authenticate_failure():
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.text = "Invalid credentials"

    with patch("httpx.Client.post", return_value=mock_resp):
        svc = WebODMService(username="wrong", password="bad")
        with pytest.raises(WebODMAuthenticationError):
            svc.authenticate()


def test_create_task_mock():
    mock_auth_resp = MagicMock()
    mock_auth_resp.status_code = 200
    mock_auth_resp.json.return_value = {"token": "valid_token"}

    mock_proj_resp = MagicMock()
    mock_proj_resp.status_code = 200
    mock_proj_resp.json.return_value = [{"id": 1, "name": "AgriDrone AutoMap"}]

    mock_task_resp = MagicMock()
    mock_task_resp.status_code = 201
    mock_task_resp.json.return_value = {"id": "odm-task-uuid-9999"}

    def mock_post(url, *args, **kwargs):
        if "token-auth" in url:
            return mock_auth_resp
        return mock_task_resp

    def mock_get(url, *args, **kwargs):
        return mock_proj_resp

    with patch("httpx.Client.post", side_effect=mock_post), patch("httpx.Client.get", side_effect=mock_get):
        svc = WebODMService()
        images = [("img1.jpg", b"fake_jpeg_1"), ("img2.jpg", b"fake_jpeg_2")]
        opts = svc.build_options_payload()
        task_uuid = svc.create_task("TestTask", images, opts)
        assert task_uuid == "odm-task-uuid-9999"


def test_get_task_status_mock():
    mock_status_resp = MagicMock()
    mock_status_resp.status_code = 200
    mock_status_resp.json.return_value = {
        "status": 20,
        "progress": 65,
        "status_text": "Point Cloud Densification",
        "processing_time": 420000,
        "available_assets": ["orthophoto.tif"],
    }

    mock_proj_resp = MagicMock()
    mock_proj_resp.status_code = 200
    mock_proj_resp.json.return_value = [{"id": 1, "name": "AgriDrone AutoMap"}]

    with patch("httpx.Client.get", side_effect=[mock_proj_resp, mock_status_resp]), patch.object(WebODMService, "authenticate", return_value="tok"):
        svc = WebODMService()
        status_data = svc.get_task_status("odm-task-uuid-9999")

        assert status_data["status"] == "RUNNING"
        assert status_data["progress_percent"] == 65
        assert "Point Cloud" in status_data["current_stage"]
