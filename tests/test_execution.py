"""Tests for SQL execution engine"""

import pytest
import sqlite3
from backend.services import ExecutionEngine


@pytest.fixture
def engine():
    """Create in-memory execution engine with sample schema"""
    eng = ExecutionEngine(":memory:")
    eng.connect()

    # Load sample schema
    schema_sql = """
    CREATE TABLE users (
        id INTEGER PRIMARY KEY,
        name TEXT,
        email TEXT UNIQUE,
        age INTEGER
    );

    CREATE TABLE orders (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        amount REAL,
        created_at TEXT
    );
    """
    eng.load_schema(schema_sql)

    # Insert sample data
    eng.insert_sample_data(
        "users",
        ["name", "email", "age"],
        [
            ("Alice", "alice@example.com", 30),
            ("Bob", "bob@example.com", 25),
            ("Charlie", "charlie@example.com", 35),
        ]
    )

    eng.insert_sample_data(
        "orders",
        ["user_id", "amount", "created_at"],
        [
            (1, 100.0, "2024-01-01"),
            (1, 200.0, "2024-01-02"),
            (2, 50.0, "2024-01-03"),
            (3, 300.0, "2024-01-04"),
        ]
    )

    yield eng
    eng.disconnect()


def test_engine_connect(engine):
    """Test engine connection"""
    assert engine.connection is not None


def test_load_schema(engine):
    """Test schema loading"""
    tables = engine.get_all_tables()
    assert "users" in tables
    assert "orders" in tables


def test_simple_select(engine):
    """Test simple SELECT query"""
    success, result, error = engine.execute("SELECT * FROM users;")

    assert success is True
    assert error is None
    assert isinstance(result, list)
    assert len(result) == 3


def test_select_with_where(engine):
    """Test SELECT with WHERE clause"""
    success, result, error = engine.execute("SELECT * FROM users WHERE age > 28;")

    assert success is True
    assert len(result) == 2  # Alice (30) and Charlie (35)


def test_select_count(engine):
    """Test COUNT aggregate"""
    success, result, error = engine.execute("SELECT COUNT(*) as user_count FROM users;")

    assert success is True
    assert len(result) == 1
    assert result[0]["user_count"] == 3


def test_select_avg(engine):
    """Test AVG aggregate"""
    success, result, error = engine.execute("SELECT AVG(age) as avg_age FROM users;")

    assert success is True
    assert len(result) == 1
    assert result[0]["avg_age"] == 30.0  # (30 + 25 + 35) / 3


def test_select_sum(engine):
    """Test SUM aggregate"""
    success, result, error = engine.execute("SELECT SUM(amount) as total FROM orders;")

    assert success is True
    assert result[0]["total"] == 650.0


def test_select_group_by(engine):
    """Test GROUP BY"""
    success, result, error = engine.execute(
        "SELECT user_id, COUNT(*) as order_count FROM orders GROUP BY user_id ORDER BY user_id;"
    )

    assert success is True
    assert len(result) == 3
    assert result[0]["order_count"] == 2  # User 1 has 2 orders


def test_select_join(engine):
    """Test JOIN"""
    success, result, error = engine.execute("""
        SELECT u.name, COUNT(o.id) as order_count, SUM(o.amount) as total_spent
        FROM users u
        LEFT JOIN orders o ON u.id = o.user_id
        GROUP BY u.id, u.name
        ORDER BY u.id;
    """)

    assert success is True
    assert len(result) == 3
    assert result[0]["name"] == "Alice"
    assert result[0]["order_count"] == 2


def test_select_limit(engine):
    """Test LIMIT"""
    success, result, error = engine.execute("SELECT * FROM users LIMIT 2;")

    assert success is True
    assert len(result) == 2


def test_select_order_by(engine):
    """Test ORDER BY"""
    success, result, error = engine.execute("SELECT * FROM users ORDER BY age DESC;")

    assert success is True
    assert result[0]["age"] == 35  # Charlie
    assert result[1]["age"] == 30  # Alice
    assert result[2]["age"] == 25  # Bob


def test_empty_select(engine):
    """Test SELECT with no results"""
    success, result, error = engine.execute("SELECT * FROM users WHERE age > 100;")

    assert success is True
    assert len(result) == 0


def test_invalid_sql_fails(engine):
    """Test that invalid SQL fails"""
    success, result, error = engine.execute("SELECT * FROM nonexistent_table;")

    assert success is False
    assert error is not None
    assert "no such table" in error.lower()


def test_empty_query_fails(engine):
    """Test that empty query fails"""
    success, result, error = engine.execute("")

    assert success is False
    assert "empty" in error.lower()


def test_context_manager(engine):
    """Test context manager usage"""
    with ExecutionEngine(":memory:") as eng:
        assert eng.connection is not None
        schema = "CREATE TABLE test (id INT);"
        success, err = eng.load_schema(schema)
        assert success is True
        assert "test" in eng.get_all_tables()


def test_format_result_list(engine):
    """Test result formatting for list"""
    success, result, _ = engine.execute("SELECT * FROM users;")
    formatted = engine.format_result(result)

    assert formatted is not None
    assert "Alice" in formatted
    assert "Bob" in formatted


def test_execute_and_format(engine):
    """Test execute_and_format method"""
    result = engine.execute_and_format("SELECT COUNT(*) as count FROM users;")

    assert result["success"] is True
    assert result["error"] is None
    assert result["row_count"] == 1
    assert result["result_json"] is not None


def test_get_table_info(engine):
    """Test getting table information"""
    info = engine.get_table_info("users")

    assert info["name"] == "users"
    assert len(info["columns"]) == 4
    column_names = [c["name"] for c in info["columns"]]
    assert "id" in column_names
    assert "name" in column_names
    assert "email" in column_names
    assert "age" in column_names


def test_insert_multiple_rows(engine):
    """Test inserting multiple rows"""
    success, error = engine.insert_sample_data(
        "users",
        ["name", "email", "age"],
        [
            ("David", "david@example.com", 40),
            ("Eve", "eve@example.com", 28),
        ]
    )

    assert success is True
    assert error is None

    # Verify insertion
    success, result, _ = engine.execute("SELECT COUNT(*) as count FROM users;")
    assert result[0]["count"] == 5


def test_query_with_string_data(engine):
    """Test query with string filtering"""
    success, result, error = engine.execute(
        "SELECT * FROM users WHERE email LIKE '%example.com%';"
    )

    assert success is True
    assert len(result) == 3


def test_union_query(engine):
    """Test UNION queries"""
    success, result, error = engine.execute("""
        SELECT name FROM users WHERE age > 30
        UNION
        SELECT name FROM users WHERE age < 26;
    """)

    assert success is True
    assert len(result) == 2  # Charlie (35) and Bob (25)


def test_distinct_query(engine):
    """Test DISTINCT"""
    success, result, error = engine.execute(
        "SELECT DISTINCT age FROM users ORDER BY age;"
    )

    assert success is True
    assert len(result) == 3


def test_case_statement(engine):
    """Test CASE statement"""
    success, result, error = engine.execute("""
        SELECT name,
               CASE WHEN age >= 30 THEN 'Senior'
                    WHEN age >= 25 THEN 'Mid'
                    ELSE 'Junior' END as category
        FROM users
        ORDER BY age DESC;
    """)

    assert success is True
    assert result[0]["category"] == "Senior"  # Charlie


def test_multiple_aggregate_functions(engine):
    """Test multiple aggregates in one query"""
    success, result, error = engine.execute("""
        SELECT
            COUNT(*) as total_orders,
            SUM(amount) as total_amount,
            AVG(amount) as avg_amount,
            MIN(amount) as min_amount,
            MAX(amount) as max_amount
        FROM orders;
    """)

    assert success is True
    assert result[0]["total_orders"] == 4
    assert result[0]["total_amount"] == 650.0
    assert result[0]["avg_amount"] == 162.5
    assert result[0]["min_amount"] == 50.0
    assert result[0]["max_amount"] == 300.0


def test_get_all_tables(engine):
    """Test getting list of all tables"""
    tables = engine.get_all_tables()

    assert isinstance(tables, list)
    assert "users" in tables
    assert "orders" in tables
