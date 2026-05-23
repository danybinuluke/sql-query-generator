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


def test_decimal_data_type():
    """Test query with DECIMAL data type"""
    with ExecutionEngine(":memory:") as eng:
        eng.load_schema("""
            CREATE TABLE prices (
                id INT,
                product_name VARCHAR(100),
                price DECIMAL(10, 2)
            );
        """)

        eng.execute("INSERT INTO prices VALUES (1, 'Widget', 19.99);")
        eng.execute("INSERT INTO prices VALUES (2, 'Gadget', 99.99);")

        success, result, error = eng.execute("SELECT product_name, price FROM prices ORDER BY price;")

        assert success is True
        assert len(result) == 2
        assert result[0]["product_name"] == "Widget"
        # SQLite stores DECIMAL as REAL, so compare as floats
        assert abs(float(result[0]["price"]) - 19.99) < 0.01


def test_date_data_type():
    """Test query with DATE data type"""
    with ExecutionEngine(":memory:") as eng:
        eng.load_schema("""
            CREATE TABLE events (
                id INT,
                event_name VARCHAR(100),
                event_date DATE
            );
        """)

        eng.execute("INSERT INTO events VALUES (1, 'Meeting', '2025-03-15');")
        eng.execute("INSERT INTO events VALUES (2, 'Conference', '2025-04-20');")

        success, result, error = eng.execute("SELECT event_name, event_date FROM events ORDER BY event_date;")

        assert success is True
        assert len(result) == 2
        assert result[0]["event_name"] == "Meeting"
        assert result[0]["event_date"] == "2025-03-15"


def test_null_values_in_aggregates():
    """Test aggregate functions with NULL values"""
    with ExecutionEngine(":memory:") as eng:
        eng.load_schema("""
            CREATE TABLE sales (
                id INT,
                amount FLOAT,
                commission FLOAT
            );
        """)

        eng.execute("INSERT INTO sales VALUES (1, 100.0, 10.0);")
        eng.execute("INSERT INTO sales VALUES (2, 200.0, NULL);")
        eng.execute("INSERT INTO sales VALUES (3, 150.0, 15.0);")

        success, result, error = eng.execute("""
            SELECT
                COUNT(*) as total_rows,
                COUNT(commission) as non_null_commission,
                SUM(commission) as total_commission
            FROM sales;
        """)

        assert success is True
        assert result[0]["total_rows"] == 3
        assert result[0]["non_null_commission"] == 2
        assert result[0]["total_commission"] == 25.0


def test_null_in_where_clause():
    """Test NULL handling in WHERE clause"""
    with ExecutionEngine(":memory:") as eng:
        eng.load_schema("""
            CREATE TABLE products (
                id INT,
                name VARCHAR(100),
                discontinued INT
            );
        """)

        eng.execute("INSERT INTO products VALUES (1, 'Product A', 0);")
        eng.execute("INSERT INTO products VALUES (2, 'Product B', 1);")
        eng.execute("INSERT INTO products VALUES (3, 'Product C', NULL);")

        success, result, error = eng.execute("SELECT name FROM products WHERE discontinued IS NULL;")

        assert success is True
        assert len(result) == 1
        assert result[0]["name"] == "Product C"


def test_self_join_query():
    """Test self-join with table aliases"""
    with ExecutionEngine(":memory:") as eng:
        eng.load_schema("""
            CREATE TABLE employees (
                id INT,
                name VARCHAR(100),
                manager_id INT
            );
        """)

        eng.execute("INSERT INTO employees VALUES (1, 'Alice', NULL);")
        eng.execute("INSERT INTO employees VALUES (2, 'Bob', 1);")
        eng.execute("INSERT INTO employees VALUES (3, 'Charlie', 1);")

        success, result, error = eng.execute("""
            SELECT e.name as employee, m.name as manager
            FROM employees e
            LEFT JOIN employees m ON e.manager_id = m.id
            ORDER BY e.name;
        """)

        assert success is True
        assert len(result) == 3
        assert result[0]["employee"] == "Alice"
        assert result[0]["manager"] is None
        assert result[1]["employee"] == "Bob"
        assert result[1]["manager"] == "Alice"


def test_multi_way_join():
    """Test joining three tables"""
    with ExecutionEngine(":memory:") as eng:
        eng.load_schema("""
            CREATE TABLE categories (id INT, name VARCHAR(100));
            CREATE TABLE products (id INT, category_id INT, name VARCHAR(100), price FLOAT);
            CREATE TABLE orders (id INT, product_id INT, quantity INT);
        """)

        eng.execute("INSERT INTO categories VALUES (1, 'Electronics');")
        eng.execute("INSERT INTO products VALUES (1, 1, 'Laptop', 999.99);")
        eng.execute("INSERT INTO orders VALUES (1, 1, 2);")

        success, result, error = eng.execute("""
            SELECT c.name as category, p.name as product, o.quantity
            FROM orders o
            JOIN products p ON o.product_id = p.id
            JOIN categories c ON p.category_id = c.id;
        """)

        assert success is True
        assert len(result) == 1
        assert result[0]["category"] == "Electronics"
        assert result[0]["product"] == "Laptop"
        assert result[0]["quantity"] == 2


def test_outer_join_variations():
    """Test different types of OUTER JOINs"""
    with ExecutionEngine(":memory:") as eng:
        eng.load_schema("""
            CREATE TABLE departments (id INT, name VARCHAR(100));
            CREATE TABLE staff (id INT, department_id INT, name VARCHAR(100));
        """)

        eng.execute("INSERT INTO departments VALUES (1, 'HR');")
        eng.execute("INSERT INTO departments VALUES (2, 'IT');")
        eng.execute("INSERT INTO staff VALUES (1, 1, 'John');")

        success, result, error = eng.execute("""
            SELECT d.name as department, s.name as staff
            FROM departments d
            LEFT JOIN staff s ON d.id = s.department_id
            ORDER BY d.name;
        """)

        assert success is True
        assert len(result) == 2
        assert result[0]["department"] == "HR"
        assert result[0]["staff"] == "John"
        assert result[1]["department"] == "IT"
        assert result[1]["staff"] is None


def test_having_clause():
    """Test HAVING clause with GROUP BY"""
    with ExecutionEngine(":memory:") as eng:
        eng.load_schema("""
            CREATE TABLE transactions (
                id INT,
                customer_id INT,
                amount FLOAT
            );
        """)

        eng.execute("INSERT INTO transactions VALUES (1, 1, 50.0);")
        eng.execute("INSERT INTO transactions VALUES (2, 1, 75.0);")
        eng.execute("INSERT INTO transactions VALUES (3, 2, 100.0);")

        success, result, error = eng.execute("""
            SELECT customer_id, SUM(amount) as total
            FROM transactions
            GROUP BY customer_id
            HAVING SUM(amount) > 100;
        """)

        assert success is True
        assert len(result) == 1
        assert result[0]["customer_id"] == 1
        assert result[0]["total"] == 125.0


def test_subquery_in_where():
    """Test subquery in WHERE clause"""
    with ExecutionEngine(":memory:") as eng:
        eng.load_schema("""
            CREATE TABLE test_users (id INT, name VARCHAR(100));
            CREATE TABLE test_orders (id INT, user_id INT, amount FLOAT);
        """)

        eng.execute("INSERT INTO test_users VALUES (1, 'Alice'), (2, 'Bob');")
        eng.execute("INSERT INTO test_orders VALUES (1, 1, 100.0), (2, 1, 200.0), (3, 2, 50.0);")

        success, result, error = eng.execute("""
            SELECT name FROM test_users
            WHERE id IN (SELECT user_id FROM test_orders WHERE amount > 100);
        """)

        assert success is True
        assert len(result) == 1
        assert result[0]["name"] == "Alice"


def test_distinct_with_null():
    """Test DISTINCT with NULL values"""
    with ExecutionEngine(":memory:") as eng:
        eng.load_schema("""
            CREATE TABLE tags (id INT, item_id INT, tag_name VARCHAR(100));
        """)

        eng.execute("INSERT INTO tags VALUES (1, 1, 'popular');")
        eng.execute("INSERT INTO tags VALUES (2, 1, 'popular');")
        eng.execute("INSERT INTO tags VALUES (3, 2, NULL);")
        eng.execute("INSERT INTO tags VALUES (4, 2, NULL);")

        success, result, error = eng.execute("SELECT DISTINCT tag_name FROM tags ORDER BY tag_name;")

        assert success is True
        assert len(result) == 2
        # DISTINCT includes NULL as a distinct value
        assert result[0]["tag_name"] is None or result[0]["tag_name"] == "popular"


def test_case_expression_aggregation():
    """Test CASE expression with aggregates"""
    with ExecutionEngine(":memory:") as eng:
        eng.load_schema("""
            CREATE TABLE survey_responses (
                id INT,
                response VARCHAR(10)
            );
        """)

        eng.execute("INSERT INTO survey_responses VALUES (1, 'yes'), (2, 'no'), (3, 'yes'), (4, 'maybe');")

        success, result, error = eng.execute("""
            SELECT
                SUM(CASE WHEN response = 'yes' THEN 1 ELSE 0 END) as yes_count,
                SUM(CASE WHEN response = 'no' THEN 1 ELSE 0 END) as no_count
            FROM survey_responses;
        """)

        assert success is True
        assert result[0]["yes_count"] == 2
        assert result[0]["no_count"] == 1


def test_window_function_alternative():
    """Test ranking with aggregates (SQL alternative to window functions)"""
    with ExecutionEngine(":memory:") as eng:
        eng.load_schema("""
            CREATE TABLE rankings (
                category VARCHAR(100),
                score INT
            );
        """)

        eng.execute("INSERT INTO rankings VALUES ('A', 100), ('A', 95), ('B', 110), ('B', 105);")

        success, result, error = eng.execute("""
            SELECT category, MAX(score) as highest_score
            FROM rankings
            GROUP BY category
            ORDER BY highest_score DESC;
        """)

        assert success is True
        assert len(result) == 2
        assert result[0]["highest_score"] == 110


def test_string_functions():
    """Test string manipulation in queries"""
    with ExecutionEngine(":memory:") as eng:
        eng.load_schema("""
            CREATE TABLE test_users (
                id INT,
                first_name VARCHAR(50),
                last_name VARCHAR(50)
            );
        """)

        eng.execute("INSERT INTO test_users VALUES (1, 'John', 'Doe'), (2, 'Jane', 'Smith');")

        success, result, error = eng.execute("""
            SELECT id, first_name || ' ' || last_name as full_name
            FROM test_users
            ORDER BY id;
        """)

        assert success is True
        assert result[0]["full_name"] == "John Doe"
        assert result[1]["full_name"] == "Jane Smith"


def test_large_result_set():
    """Test query returning large number of rows"""
    with ExecutionEngine(":memory:") as eng:
        eng.load_schema("""
            CREATE TABLE numbers (id INT, value INT);
        """)

        # Insert 1000 rows
        for i in range(1000):
            eng.execute(f"INSERT INTO numbers VALUES ({i}, {i * 2});")

        success, result, error = eng.execute("SELECT COUNT(*) as total FROM numbers;")

        assert success is True
        assert result[0]["total"] == 1000


def test_large_result_with_limit():
    """Test LIMIT on large result set"""
    with ExecutionEngine(":memory:") as eng:
        eng.load_schema("""
            CREATE TABLE items (id INT);
        """)

        for i in range(500):
            eng.execute(f"INSERT INTO items VALUES ({i});")

        success, result, error = eng.execute("SELECT id FROM items LIMIT 10 OFFSET 50;")

        assert success is True
        assert len(result) == 10
        assert result[0]["id"] == 50


def test_empty_schema_in_memory():
    """Test querying empty tables"""
    with ExecutionEngine(":memory:") as eng:
        eng.load_schema("""
            CREATE TABLE empty_table (id INT, name VARCHAR(100));
        """)

        success, result, error = eng.execute("SELECT * FROM empty_table;")

        assert success is True
        assert len(result) == 0


def test_complex_where_conditions():
    """Test complex WHERE clauses with AND/OR"""
    with ExecutionEngine(":memory:") as eng:
        eng.load_schema("""
            CREATE TABLE test_products (
                id INT,
                name VARCHAR(100),
                price FLOAT,
                stock INT,
                category VARCHAR(50)
            );
        """)

        eng.execute("INSERT INTO test_products VALUES (1, 'Item A', 10.0, 5, 'X');")
        eng.execute("INSERT INTO test_products VALUES (2, 'Item B', 20.0, 15, 'Y');")
        eng.execute("INSERT INTO test_products VALUES (3, 'Item C', 15.0, 3, 'X');")

        success, result, error = eng.execute("""
            SELECT name FROM test_products
            WHERE (price > 12 AND category = 'X') OR (stock > 10 AND category = 'Y')
            ORDER BY name;
        """)

        assert success is True
        assert len(result) == 2
        assert result[0]["name"] == "Item B"
        assert result[1]["name"] == "Item C"


def test_transaction_isolation(engine):
    """Test that each ExecutionEngine instance is isolated"""
    engine.load_schema("""
        CREATE TABLE state (id INT, value INT);
    """)

    engine.execute("INSERT INTO state VALUES (1, 100);")

    # Create new engine instance - should have separate in-memory database
    with ExecutionEngine(":memory:") as engine2:
        engine2.load_schema("""
            CREATE TABLE state (id INT, value INT);
        """)
        success, result, error = engine2.execute("SELECT COUNT(*) as count FROM state;")

        assert success is True
        assert result[0]["count"] == 0  # Different database, no data


def test_format_result_with_mixed_types():
    """Test result formatting with mixed data types"""
    import json
    with ExecutionEngine(":memory:") as eng:
        eng.load_schema("""
            CREATE TABLE mixed_data (
                id INT,
                amount FLOAT,
                active INT,
                description VARCHAR(100)
            );
        """)

        eng.execute("INSERT INTO mixed_data VALUES (1, 99.99, 1, 'Active item');")

        success, result, error = eng.execute("SELECT * FROM mixed_data;")

        assert success is True
        formatted_str = eng.format_result(result)
        formatted = json.loads(formatted_str)
        assert formatted[0]["id"] == 1
        assert formatted[0]["amount"] == 99.99
        assert formatted[0]["active"] == 1
        assert formatted[0]["description"] == "Active item"
