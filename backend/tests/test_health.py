from unittest.mock import patch
from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Verify that root endpoint returns API information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["project"] == "AgriDrone AutoMap"
    assert data["status"] == "online"
    assert "/api/v1/health" in data["health_check"]


def test_liveness_endpoint(client: TestClient):
    """Verify that liveness endpoint returns 200 OK."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"
    assert "timestamp" in data


def test_readiness_endpoint_healthy(client: TestClient):
    """Verify that readiness endpoint confirms database and redis health."""
    response = client.get("/api/v1/health/readiness")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert "database" in data["components"]
    assert "redis" in data["components"]
    assert data["components"]["database"]["status"] == "healthy"
    assert data["components"]["redis"]["status"] == "healthy"
    assert data["components"]["database"]["latency_ms"] >= 0


def test_readiness_endpoint_db_failure(client: TestClient):
    """Verify that readiness returns 503 when database is unavailable."""
    with patch("app.api.v1.endpoints.health.SessionLocal") as mock_session:
        mock_session.side_effect = Exception("Database connection timeout")
        response = client.get("/api/v1/health/readiness")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "not_ready"
        assert data["components"]["database"]["status"] == "unhealthy"
