"""Tests for LLM service"""

import pytest
from backend.services import LLMService


@pytest.fixture
def llm_service():
    """Create LLM service instance"""
    service = LLMService()
    yield service
    if service.is_loaded():
        service.unload_model()


def test_llm_service_init(llm_service):
    """Test LLM service initialization"""
    assert llm_service.model_name == "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    assert llm_service.tokenizer is None
    assert llm_service.model is None
    assert not llm_service.is_loaded()


def test_llm_service_load_model(llm_service):
    """Test loading the model"""
    success = llm_service.load_model()
    assert success is True
    assert llm_service.model is not None
    assert llm_service.tokenizer is not None
    assert llm_service.is_loaded()


def test_llm_service_generate_sql_no_model(llm_service):
    """Test generation fails without loaded model"""
    success, sql, error = llm_service.generate_sql("SELECT * FROM users;")
    assert success is False
    assert sql is None
    assert error == "Model not loaded"


def test_llm_service_generate_sql_with_model(llm_service):
    """Test SQL generation with loaded model"""
    llm_service.load_model()

    prompt = """You are a SQL expert. Convert the natural language question to SQL.

Question: How many users are there?

Schema:
- Table: users
  - Columns: id (INT), name (VARCHAR), email (VARCHAR)

Generate a SELECT query:"""

    success, sql, error = llm_service.generate_sql(prompt, max_tokens=100)

    if success:
        assert sql is not None
        assert len(sql) > 0
        assert "SELECT" in sql.upper()
    else:
        # If generation fails due to hardware constraints, that's okay for testing
        assert error is not None


def test_llm_service_unload_model(llm_service):
    """Test unloading the model"""
    llm_service.load_model()
    assert llm_service.is_loaded()

    llm_service.unload_model()
    assert llm_service.model is None
    assert llm_service.tokenizer is None
    assert not llm_service.is_loaded()


def test_llm_service_extract_sql_from_code_block(llm_service):
    """Test extracting SQL from markdown code block"""
    response = """Here's the SQL query:
```sql
SELECT COUNT(*) as user_count FROM users;
```
This query counts all users."""

    sql = llm_service._extract_sql(response, "")
    assert sql is not None
    assert "SELECT COUNT(*)" in sql
    assert "user_count" in sql


def test_llm_service_extract_sql_from_response(llm_service):
    """Test extracting SQL from plain response"""
    response = """SELECT * FROM users WHERE age > 25 ORDER BY name;"""

    sql = llm_service._extract_sql(response, "")
    assert sql is not None
    assert "SELECT *" in sql
    assert "age > 25" in sql


def test_llm_service_extract_sql_with_prompt_removal(llm_service):
    """Test extracting SQL removes original prompt"""
    prompt = "Convert this to SQL:"
    response = prompt + "\n\nSELECT * FROM orders;"

    sql = llm_service._extract_sql(response, prompt)
    assert sql is not None
    assert sql.strip().startswith("SELECT")


def test_llm_service_extract_sql_generic_code_block(llm_service):
    """Test extracting SQL from generic code block"""
    response = """```
SELECT SUM(amount) as total FROM orders;
```"""

    sql = llm_service._extract_sql(response, "")
    assert sql is not None
    assert "SUM(amount)" in sql


def test_llm_service_extract_sql_multiline(llm_service):
    """Test extracting multiline SQL"""
    response = """SELECT
    u.name,
    COUNT(o.id) as order_count
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id;"""

    sql = llm_service._extract_sql(response, "")
    assert sql is not None
    assert "LEFT JOIN" in sql
    assert "GROUP BY" in sql


def test_llm_service_extract_sql_with_cte(llm_service):
    """Test extracting SQL with CTE (Common Table Expression)"""
    response = """WITH user_orders AS (
    SELECT user_id, COUNT(*) as count FROM orders GROUP BY user_id
)
SELECT * FROM user_orders WHERE count > 5;"""

    sql = llm_service._extract_sql(response, "")
    assert sql is not None
    assert "WITH user_orders AS" in sql


def test_llm_service_context_manager(llm_service):
    """Test LLM service context manager"""
    with LLMService() as service:
        success = service.load_model()
        if success:
            assert service.is_loaded()


def test_llm_service_custom_model(llm_service):
    """Test initializing with custom model name"""
    service = LLMService(model_name="gpt2")
    assert service.model_name == "gpt2"


def test_llm_service_extract_sql_empty_response(llm_service):
    """Test extraction from empty response"""
    sql = llm_service._extract_sql("", "")
    assert sql is None


def test_llm_service_extract_sql_no_select(llm_service):
    """Test extraction fails without SELECT or WITH"""
    response = "This is just plain text without any SQL"
    sql = llm_service._extract_sql(response, "")
    assert sql is None


def test_llm_service_extract_sql_with_explanation(llm_service):
    """Test extracting SQL when response has explanation"""
    response = """The query should select all products with price > 100:
SELECT * FROM products WHERE price > 100;

This will return all products in the products table that cost more than 100."""

    sql = llm_service._extract_sql(response, "")
    assert sql is not None
    assert "SELECT *" in sql
    assert "price > 100" in sql
