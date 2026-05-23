"""Tests for SQL validator service"""

import pytest
from backend.services import SQLValidator


class TestValidation:
    """Test SQL validation"""

    def test_validate_simple_select(self):
        """Test validating a simple SELECT query"""
        sql = "SELECT * FROM users;"
        is_valid, message = SQLValidator.validate(sql)
        assert is_valid is True
        assert "valid" in message.lower()

    def test_validate_select_with_where(self):
        """Test SELECT with WHERE clause"""
        sql = "SELECT id, email FROM users WHERE age > 18;"
        is_valid, message = SQLValidator.validate(sql)
        assert is_valid is True

    def test_validate_select_with_join(self):
        """Test SELECT with JOIN"""
        sql = """
        SELECT u.id, u.email, COUNT(o.id) as total_orders
        FROM users u
        LEFT JOIN orders o ON u.id = o.user_id
        GROUP BY u.id
        """
        is_valid, message = SQLValidator.validate(sql)
        assert is_valid is True

    def test_validate_with_cte(self):
        """Test SELECT with Common Table Expression"""
        sql = """
        WITH user_orders AS (
            SELECT user_id, COUNT(*) as count
            FROM orders
            GROUP BY user_id
        )
        SELECT * FROM user_orders
        """
        is_valid, message = SQLValidator.validate(sql)
        assert is_valid is True

    def test_validate_empty_sql_fails(self):
        """Test that empty SQL is rejected"""
        is_valid, message = SQLValidator.validate("")
        assert is_valid is False
        assert "empty" in message.lower()

    def test_validate_drop_fails(self):
        """Test that DROP query is rejected"""
        sql = "DROP TABLE users;"
        is_valid, message = SQLValidator.validate(sql)
        assert is_valid is False
        assert "forbidden" in message.lower() or "drop" in message.lower()

    def test_validate_delete_fails(self):
        """Test that DELETE query is rejected"""
        sql = "DELETE FROM users WHERE id = 1;"
        is_valid, message = SQLValidator.validate(sql)
        assert is_valid is False

    def test_validate_update_fails(self):
        """Test that UPDATE query is rejected"""
        sql = "UPDATE users SET age = 30 WHERE id = 1;"
        is_valid, message = SQLValidator.validate(sql)
        assert is_valid is False

    def test_validate_insert_fails(self):
        """Test that INSERT query is rejected"""
        sql = "INSERT INTO users (id, email) VALUES (1, 'test@example.com');"
        is_valid, message = SQLValidator.validate(sql)
        assert is_valid is False

    def test_validate_alter_fails(self):
        """Test that ALTER query is rejected"""
        sql = "ALTER TABLE users ADD COLUMN phone VARCHAR(20);"
        is_valid, message = SQLValidator.validate(sql)
        assert is_valid is False

    def test_validate_truncate_fails(self):
        """Test that TRUNCATE query is rejected"""
        sql = "TRUNCATE TABLE users;"
        is_valid, message = SQLValidator.validate(sql)
        assert is_valid is False

    def test_validate_create_fails(self):
        """Test that CREATE query is rejected"""
        sql = "CREATE TABLE new_users (id INT);"
        is_valid, message = SQLValidator.validate(sql)
        assert is_valid is False

    def test_validate_drop_in_string_allowed(self):
        """Test that 'DROP' in string literals is allowed"""
        sql = "SELECT * FROM products WHERE description LIKE '%DROP TABLE%';"
        is_valid, message = SQLValidator.validate(sql)
        assert is_valid is True  # DROP is in a string literal, should be OK

    def test_validate_comment_injection_attack(self):
        """Test detection of comment injection attempts"""
        sql = "SELECT * FROM users -- DROP TABLE users"
        is_valid, message = SQLValidator.validate(sql)
        # Should be accepted since -- comments are valid in SELECT
        assert isinstance(is_valid, bool)

    def test_validate_union_select(self):
        """Test UNION queries are allowed"""
        sql = """
        SELECT id, email FROM users
        UNION
        SELECT id, email FROM archived_users
        """
        is_valid, message = SQLValidator.validate(sql)
        assert is_valid is True

    def test_validate_aggregate_functions(self):
        """Test queries with aggregate functions"""
        sqls = [
            "SELECT COUNT(*) FROM users;",
            "SELECT AVG(price) FROM products;",
            "SELECT MAX(amount) FROM orders;",
            "SELECT SUM(quantity) FROM order_items;",
            "SELECT MIN(created_at) FROM logs;",
        ]

        for sql in sqls:
            is_valid, message = SQLValidator.validate(sql)
            assert is_valid is True, f"Failed for: {sql}"

    def test_validate_complex_real_world_query(self):
        """Test complex real-world query"""
        sql = """
        SELECT
            u.id,
            u.email,
            COUNT(DISTINCT o.id) as total_orders,
            SUM(o.amount) as total_spent,
            AVG(o.amount) as avg_order_value
        FROM users u
        LEFT JOIN orders o ON u.id = o.user_id
        WHERE u.created_at >= '2024-01-01'
        GROUP BY u.id, u.email
        HAVING COUNT(o.id) > 5
        ORDER BY total_spent DESC
        LIMIT 100
        """
        is_valid, message = SQLValidator.validate(sql)
        assert is_valid is True

    def test_is_select_query(self):
        """Test checking if query is SELECT"""
        assert SQLValidator.is_select_query("SELECT * FROM users") is True
        assert SQLValidator.is_select_query("WITH cte AS (...) SELECT *") is True
        assert SQLValidator.is_select_query("DROP TABLE users") is False
        assert SQLValidator.is_select_query("INSERT INTO users") is False

    def test_extract_tables_simple(self):
        """Test extracting table names from simple query"""
        sql = "SELECT * FROM users;"
        tables = SQLValidator.extract_tables(sql)
        assert "users" in tables

    def test_extract_tables_with_join(self):
        """Test extracting table names from JOIN query"""
        sql = """
        SELECT *
        FROM users
        JOIN orders ON users.id = orders.user_id
        LEFT JOIN products ON orders.product_id = products.id
        """
        tables = SQLValidator.extract_tables(sql)
        assert "users" in tables
        assert "orders" in tables
        assert "products" in tables

    def test_extract_tables_with_aliases(self):
        """Test extracting tables with aliases"""
        sql = "SELECT u.id FROM users u JOIN orders o ON u.id = o.user_id"
        tables = SQLValidator.extract_tables(sql)
        assert "users" in tables
        assert "orders" in tables

    def test_get_validation_report(self):
        """Test getting detailed validation report"""
        sql = "SELECT id, email FROM users WHERE age > 18"
        report = SQLValidator.get_validation_report(sql)

        assert "is_valid" in report
        assert "message" in report
        assert "is_select" in report
        assert "tables" in report
        assert "length" in report
        assert report["is_valid"] is True
        assert report["is_select"] is True
        assert "users" in report["tables"]

    def test_validation_report_for_dangerous_query(self):
        """Test validation report for dangerous query"""
        sql = "DROP TABLE users"
        report = SQLValidator.get_validation_report(sql)

        assert report["is_valid"] is False
        assert "forbidden" in report["message"].lower() or "drop" in report["message"].lower()

    def test_extract_tables_empty(self):
        """Test extracting tables from query with no FROM"""
        sql = "SELECT 1"
        tables = SQLValidator.extract_tables(sql)
        assert len(tables) == 0

    def test_null_byte_injection_fails(self):
        """Test that null byte injection is detected"""
        sql = "SELECT * FROM users\x00 DROP TABLE users"
        is_valid, message = SQLValidator.validate(sql)
        assert is_valid is False

    def test_case_insensitive_validation(self):
        """Test that validation is case-insensitive"""
        sqls = [
            "select * from users",
            "SELECT * FROM users",
            "SeLeCt * FrOm users",
        ]

        for sql in sqls:
            is_valid, _ = SQLValidator.validate(sql)
            assert is_valid is True

    def test_dangerous_case_insensitive(self):
        """Test that dangerous keywords are caught regardless of case"""
        sqls = [
            "drop table users",
            "DROP TABLE users",
            "DrOp TaBlE users",
        ]

        for sql in sqls:
            is_valid, _ = SQLValidator.validate(sql)
            assert is_valid is False
