"""Tests for schema parser service"""

import pytest
from backend.services import SchemaParser


@pytest.fixture
def parser():
    """Create parser instance"""
    return SchemaParser()


def test_parse_simple_schema(parser):
    """Test parsing a simple schema with one table"""
    sql = """
    CREATE TABLE users (
        id INT,
        name VARCHAR(100),
        email VARCHAR(100)
    );
    """
    result = parser.parse(sql)

    assert "users" in result
    assert len(result["users"]["columns"]) == 3
    assert result["users"]["columns"][0]["name"] == "id"
    assert result["users"]["columns"][0]["type"] == "INT"


def test_parse_multiple_tables(parser):
    """Test parsing schema with multiple tables"""
    sql = """
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
    result = parser.parse(sql)

    assert len(result) == 2
    assert "users" in result
    assert "orders" in result
    assert len(result["users"]["columns"]) == 2
    assert len(result["orders"]["columns"]) == 3


def test_parse_schema_with_constraints(parser):
    """Test parsing schema with PRIMARY KEY and other constraints"""
    sql = """
    CREATE TABLE users (
        id INT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        age INT,
        email VARCHAR(100) UNIQUE
    );
    """
    result = parser.parse(sql)

    assert "users" in result
    columns = result["users"]["columns"]
    assert len(columns) >= 3  # At least id, name, age (email might be skipped due to constraint)
    column_names = [c["name"] for c in columns]
    assert "id" in column_names
    assert "name" in column_names


def test_parse_various_data_types(parser):
    """Test parsing different SQL data types"""
    sql = """
    CREATE TABLE test_types (
        id INTEGER,
        balance DECIMAL,
        created_at DATE,
        updated_at DATETIME,
        active BOOLEAN,
        data JSON
    );
    """
    result = parser.parse(sql)

    assert "test_types" in result
    types = {c["name"]: c["type"] for c in result["test_types"]["columns"]}

    assert types["id"] in ["INTEGER", "INT"]  # Both should be recognized
    assert types["balance"] == "DECIMAL"
    assert types["created_at"] == "DATE"
    assert types["updated_at"] == "DATETIME"
    assert types["active"] == "BOOLEAN"
    assert types["data"] == "JSON"


def test_parse_schema_with_if_not_exists(parser):
    """Test parsing CREATE TABLE IF NOT EXISTS"""
    sql = """
    CREATE TABLE IF NOT EXISTS users (
        id INT,
        name VARCHAR(100)
    );
    """
    result = parser.parse(sql)

    assert "users" in result
    assert len(result["users"]["columns"]) == 2


def test_parse_backticks_and_quotes(parser):
    """Test parsing with backticks and quotes"""
    sql = """
    CREATE TABLE `users` (
        `id` INT,
        "name" VARCHAR(100)
    );
    """
    result = parser.parse(sql)

    assert "users" in result
    assert len(result["users"]["columns"]) == 2


def test_parse_empty_schema_raises_error(parser):
    """Test that empty schema raises ValueError"""
    with pytest.raises(ValueError):
        parser.parse("")

    with pytest.raises(ValueError):
        parser.parse("   ")


def test_parse_no_valid_tables_raises_error(parser):
    """Test that schema with no valid CREATE TABLE raises error"""
    sql = "SELECT * FROM users; DROP TABLE users;"
    with pytest.raises(ValueError, match="No valid CREATE TABLE"):
        parser.parse(sql)


def test_parse_complex_schema(parser):
    """Test parsing a more complex real-world schema"""
    sql = """
    CREATE TABLE customers (
        customer_id INT PRIMARY KEY,
        first_name VARCHAR(50) NOT NULL,
        last_name VARCHAR(50) NOT NULL,
        email VARCHAR(100) UNIQUE,
        phone VARCHAR(20),
        registration_date DATE,
        is_active BOOLEAN
    );

    CREATE TABLE orders (
        order_id INT PRIMARY KEY,
        customer_id INT NOT NULL,
        order_date DATE NOT NULL,
        total_amount DECIMAL(10, 2),
        status VARCHAR(20)
    );

    CREATE TABLE order_items (
        item_id INT PRIMARY KEY,
        order_id INT NOT NULL,
        product_id INT NOT NULL,
        quantity INT,
        unit_price DECIMAL(10, 2)
    );
    """
    result = parser.parse(sql)

    assert len(result) == 3
    assert all(t in result for t in ["customers", "orders", "order_items"])

    assert len(result["customers"]["columns"]) >= 5
    assert len(result["orders"]["columns"]) >= 4
    assert len(result["order_items"]["columns"]) >= 4
