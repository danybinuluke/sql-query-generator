"""Tests for FastAPI application and endpoints"""

import pytest
from starlette.testclient import TestClient
from backend.main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


def test_health_check(client):
    """Test /health endpoint returns 200 with ok status"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_endpoint(client):
    """Test root / endpoint returns API info"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "SQLGenie API"
    assert data["status"] == "running"
    assert "endpoints" in data


def test_info_endpoint(client):
    """Test /info endpoint returns service information"""
    response = client.get("/info")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "SQLGenie"
    assert "version" in data
    assert "environment" in data


def test_openapi_docs(client):
    """Test OpenAPI documentation is available"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "info" in data


def test_docs_endpoint(client):
    """Test Swagger UI documentation is available"""
    response = client.get("/docs")
    assert response.status_code == 200
