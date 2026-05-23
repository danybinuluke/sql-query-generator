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


def test_query_with_valid_session(client):
    """Test query endpoint with valid session"""
    # First upload a schema
    sql_content = """
    CREATE TABLE users (
        id INT,
        email VARCHAR(100)
    );
    """

    upload_response = client.post(
        "/upload-schema",
        files={"file": ("schema.sql", sql_content, "text/plain")}
    )

    session_id = upload_response.json()["session_id"]

    # Now send a query
    query_response = client.post(
        "/query",
        json={
            "session_id": session_id,
            "question": "How many users are there?"
        }
    )

    assert query_response.status_code == 200
    data = query_response.json()
    assert data["session_id"] == session_id


def test_query_with_invalid_session(client):
    """Test query endpoint with non-existent session"""
    response = client.post(
        "/query",
        json={
            "session_id": "nonexistent-session-id",
            "question": "How many users?"
        }
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_query_with_empty_question(client):
    """Test query endpoint with empty question"""
    # Upload schema first
    sql_content = "CREATE TABLE users (id INT);"

    upload_response = client.post(
        "/upload-schema",
        files={"file": ("schema.sql", sql_content, "text/plain")}
    )

    session_id = upload_response.json()["session_id"]

    # Send query with empty question
    response = client.post(
        "/query",
        json={
            "session_id": session_id,
            "question": ""
        }
    )

    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower()


def test_query_with_very_long_question(client):
    """Test query endpoint with excessively long question"""
    # Upload schema first
    sql_content = "CREATE TABLE users (id INT);"

    upload_response = client.post(
        "/upload-schema",
        files={"file": ("schema.sql", sql_content, "text/plain")}
    )

    session_id = upload_response.json()["session_id"]

    # Send query with very long question
    long_question = "What " * 300  # Very long

    response = client.post(
        "/query",
        json={
            "session_id": session_id,
            "question": long_question
        }
    )

    assert response.status_code == 400


def test_query_response_format(client):
    """Test that query response has correct format"""
    # Upload schema
    sql_content = """
    CREATE TABLE orders (
        id INT,
        amount FLOAT
    );
    """

    upload_response = client.post(
        "/upload-schema",
        files={"file": ("schema.sql", sql_content, "text/plain")}
    )

    session_id = upload_response.json()["session_id"]

    # Query
    query_response = client.post(
        "/query",
        json={
            "session_id": session_id,
            "question": "What is the total amount?"
        }
    )

    assert query_response.status_code == 200
    data = query_response.json()

    # Verify response structure
    assert "session_id" in data
    assert "generated_sql" in data
    assert "result" in data
    assert "error" in data
    assert isinstance(data["session_id"], str)
    assert isinstance(data["generated_sql"], str)


def test_query_increments_query_count(client):
    """Test that query increments the query count in session"""
    # Upload schema
    sql_content = "CREATE TABLE test (id INT);"

    upload_response = client.post(
        "/upload-schema",
        files={"file": ("schema.sql", sql_content, "text/plain")}
    )

    session_id = upload_response.json()["session_id"]

    # Send multiple queries
    for i in range(3):
        response = client.post(
            "/query",
            json={
                "session_id": session_id,
                "question": f"Question {i}?"
            }
        )
        assert response.status_code == 200


def test_query_with_multiple_tables(client):
    """Test query with multi-table schema"""
    sql_content = """
    CREATE TABLE users (id INT, email VARCHAR(100));
    CREATE TABLE orders (id INT, user_id INT, amount FLOAT);
    """

    upload_response = client.post(
        "/upload-schema",
        files={"file": ("schema.sql", sql_content, "text/plain")}
    )

    session_id = upload_response.json()["session_id"]

    query_response = client.post(
        "/query",
        json={
            "session_id": session_id,
            "question": "Join users and orders"
        }
    )

    assert query_response.status_code == 200
    data = query_response.json()
    assert data["session_id"] == session_id


def test_upload_and_query_integration(client):
    """Test full integration: upload schema and query"""
    # Upload schema
    sql_content = """
    CREATE TABLE products (
        id INT,
        name VARCHAR(100),
        price FLOAT,
        category VARCHAR(50)
    );
    """

    upload_response = client.post(
        "/upload-schema",
        files={"file": ("schema.sql", sql_content, "text/plain")}
    )

    assert upload_response.status_code == 200
    upload_data = upload_response.json()
    session_id = upload_data["session_id"]

    # Verify uploaded schema
    assert upload_data["table_count"] == 1
    assert upload_data["tables"][0]["name"] == "products"

    # Query the schema
    query_response = client.post(
        "/query",
        json={
            "session_id": session_id,
            "question": "Show me all products in the electronics category"
        }
    )

    assert query_response.status_code == 200
    query_data = query_response.json()

    # Verify query response
    assert query_data["session_id"] == session_id
    assert query_data["error"] is None
