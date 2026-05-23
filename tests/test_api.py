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


def test_upload_schema_valid(client):
    """Test uploading a valid SQL schema"""
    sql_content = """
    CREATE TABLE users (
        id INT,
        name VARCHAR(100),
        email VARCHAR(100)
    );
    """

    response = client.post(
        "/upload-schema",
        files={"file": ("schema.sql", sql_content, "text/plain")}
    )

    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["table_count"] == 1
    assert len(data["tables"]) == 1
    assert data["tables"][0]["name"] == "users"
    assert len(data["tables"][0]["columns"]) == 3


def test_upload_schema_multiple_tables(client):
    """Test uploading schema with multiple tables"""
    sql_content = """
    CREATE TABLE users (
        id INT,
        email VARCHAR(100)
    );

    CREATE TABLE orders (
        id INT,
        user_id INT,
        amount FLOAT
    );
    """

    response = client.post(
        "/upload-schema",
        files={"file": ("schema.sql", sql_content, "text/plain")}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["table_count"] == 2
    assert len(data["tables"]) == 2
    table_names = {t["name"] for t in data["tables"]}
    assert "users" in table_names
    assert "orders" in table_names


def test_upload_schema_wrong_file_type(client):
    """Test that non-.sql files are rejected"""
    response = client.post(
        "/upload-schema",
        files={"file": ("schema.json", '{"tables": []}', "application/json")}
    )

    assert response.status_code == 400
    assert "must be a .sql file" in response.json()["detail"]


def test_upload_schema_empty_file(client):
    """Test that empty schema is rejected"""
    response = client.post(
        "/upload-schema",
        files={"file": ("schema.sql", "", "text/plain")}
    )

    assert response.status_code == 400
    assert "parsing error" in response.json()["detail"].lower()


def test_upload_schema_no_valid_tables(client):
    """Test that files with no CREATE TABLE are rejected"""
    sql_content = "SELECT * FROM users; DROP TABLE users;"

    response = client.post(
        "/upload-schema",
        files={"file": ("schema.sql", sql_content, "text/plain")}
    )

    assert response.status_code == 400
    assert "No valid CREATE TABLE" in response.json()["detail"]


def test_upload_schema_response_format(client):
    """Test that response has correct format and fields"""
    sql_content = """
    CREATE TABLE products (
        id INT,
        name VARCHAR(100),
        price FLOAT,
        created_at DATE
    );
    """

    response = client.post(
        "/upload-schema",
        files={"file": ("schema.sql", sql_content, "text/plain")}
    )

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert isinstance(data["session_id"], str)
    assert len(data["session_id"]) > 0
    assert isinstance(data["tables"], list)
    assert isinstance(data["table_count"], int)
    assert isinstance(data["message"], str)

    # Verify table structure
    table = data["tables"][0]
    assert table["name"] == "products"
    assert isinstance(table["columns"], list)

    # Verify column structure
    for col in table["columns"]:
        assert "name" in col
        assert "type" in col
        assert isinstance(col["name"], str)
        assert isinstance(col["type"], str)
