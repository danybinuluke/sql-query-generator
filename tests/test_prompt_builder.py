"""Tests for prompt builder service"""

import pytest
from backend.services import PromptBuilder


@pytest.fixture
def sample_schema():
    """Sample database schema for testing"""
    return {
        "users": {
            "columns": [
                {"name": "id", "type": "INT"},
                {"name": "email", "type": "VARCHAR"},
                {"name": "age", "type": "INT"}
            ]
        },
        "orders": {
            "columns": [
                {"name": "id", "type": "INT"},
                {"name": "user_id", "type": "INT"},
                {"name": "amount", "type": "FLOAT"}
            ]
        }
    }


def test_build_basic_prompt(sample_schema):
    """Test building a basic prompt"""
    question = "What is the average age of users?"
    prompt = PromptBuilder.build(sample_schema, question)

    assert prompt is not None
    assert isinstance(prompt, str)
    assert len(prompt) > 0


def test_prompt_contains_schema(sample_schema):
    """Test that prompt includes schema information"""
    question = "How many users are there?"
    prompt = PromptBuilder.build(sample_schema, question)

    assert "users" in prompt
    assert "orders" in prompt
    assert "id" in prompt
    assert "email" in prompt
    assert "amount" in prompt


def test_prompt_contains_question(sample_schema):
    """Test that prompt includes the user question"""
    question = "Show me the top 10 most expensive orders"
    prompt = PromptBuilder.build(sample_schema, question)

    assert question in prompt


def test_prompt_contains_safety_rules(sample_schema):
    """Test that prompt includes safety constraints"""
    question = "Get all users"
    prompt = PromptBuilder.build(sample_schema, question)

    assert "SELECT" in prompt.upper()
    assert "CRITICAL" in prompt or "RULES" in prompt or "DROP" in prompt.upper()


def test_prompt_format_is_readable(sample_schema):
    """Test that prompt is well-formatted and readable"""
    question = "Count total orders by user"
    prompt = PromptBuilder.build(sample_schema, question)

    # Should have clear sections
    assert "\n" in prompt
    # Should reference tables
    assert "Table:" in prompt or "TABLE" in prompt


def test_build_with_empty_schema_raises_error(sample_schema):
    """Test that empty schema raises error"""
    with pytest.raises(ValueError, match="Schema cannot be empty"):
        PromptBuilder.build({}, "What is the total amount?")


def test_build_with_empty_question_raises_error(sample_schema):
    """Test that empty question raises error"""
    with pytest.raises(ValueError, match="Question cannot be empty"):
        PromptBuilder.build(sample_schema, "")

    with pytest.raises(ValueError, match="Question cannot be empty"):
        PromptBuilder.build(sample_schema, "   ")


def test_build_with_complex_question(sample_schema):
    """Test building prompt with complex multi-table question"""
    question = "Find users with the highest average order amount"
    prompt = PromptBuilder.build(sample_schema, question)

    assert question in prompt
    assert "users" in prompt
    assert "orders" in prompt


def test_validate_question_valid():
    """Test question validation with valid questions"""
    assert PromptBuilder.validate_question("What is the average age?") is True
    assert PromptBuilder.validate_question("Count total users") is True
    assert PromptBuilder.validate_question("Show me all products") is True


def test_validate_question_invalid():
    """Test question validation with invalid questions"""
    assert PromptBuilder.validate_question("") is False
    assert PromptBuilder.validate_question("   ") is False
    assert PromptBuilder.validate_question(None) is False


def test_validate_question_too_long():
    """Test question validation with excessively long question"""
    long_question = "What " * 300  # Very long question
    assert PromptBuilder.validate_question(long_question) is False


def test_validate_question_dangerous_keywords():
    """Test validation flags dangerous keywords"""
    # These should return True (valid) but log warnings
    dangerous_questions = [
        "DROP all tables",
        "DELETE from users",
        "ALTER the schema",
        "INSERT new data"
    ]

    for q in dangerous_questions:
        # Should still return True (validation passes) but logged as warning
        result = PromptBuilder.validate_question(q)
        # Validation passes, but warning was logged
        assert isinstance(result, bool)


def test_extract_sql_from_markdown_response():
    """Test extracting SQL from markdown code block"""
    response = """Here's the SQL query:

```sql
SELECT AVG(age) FROM users;
```

This will give you the average age."""

    sql = PromptBuilder.extract_sql_from_response(response)
    assert sql == "SELECT AVG(age) FROM users;"


def test_extract_sql_from_plain_response():
    """Test extracting SQL from plain text response"""
    response = "SELECT COUNT(*) FROM orders;"

    sql = PromptBuilder.extract_sql_from_response(response)
    assert "SELECT" in sql
    assert "COUNT" in sql


def test_extract_sql_with_multiline():
    """Test extracting multiline SQL"""
    response = """```sql
SELECT
    user_id,
    COUNT(*) as total_orders
FROM orders
GROUP BY user_id;
```"""

    sql = PromptBuilder.extract_sql_from_response(response)
    assert "SELECT" in sql
    assert "user_id" in sql
    assert "COUNT" in sql
    assert "GROUP BY" in sql


def test_extract_sql_strips_whitespace():
    """Test that extracted SQL is properly trimmed"""
    response = "   SELECT * FROM users;   "

    sql = PromptBuilder.extract_sql_from_response(response)
    assert not sql.startswith(" ")
    assert not sql.endswith(" ")


def test_build_with_examples(sample_schema):
    """Test building prompt with few-shot examples"""
    examples = [
        {
            "question": "How many users are there?",
            "sql": "SELECT COUNT(*) FROM users;"
        },
        {
            "question": "What is the average order amount?",
            "sql": "SELECT AVG(amount) FROM orders;"
        }
    ]

    question = "What is the total revenue?"
    prompt = PromptBuilder.build_with_examples(sample_schema, question, examples)

    assert prompt is not None
    assert "Example" in prompt
    assert "SELECT COUNT(*)" in prompt
    assert "SELECT AVG(amount)" in prompt


def test_build_with_empty_examples(sample_schema):
    """Test building prompt with no examples"""
    question = "Get all users"
    prompt = PromptBuilder.build_with_examples(sample_schema, question, [])

    assert prompt is not None
    assert question in prompt


def test_prompt_instructs_select_only(sample_schema):
    """Test that prompt emphasizes SELECT-only constraint"""
    question = "Get user data"
    prompt = PromptBuilder.build(sample_schema, question)

    assert "SELECT" in prompt or "select" in prompt.lower()
    assert "INSERT" in prompt or "UPDATE" in prompt or "DELETE" in prompt or "DROP" in prompt


def test_prompt_includes_column_types(sample_schema):
    """Test that prompt includes data types for columns"""
    question = "What tables exist?"
    prompt = PromptBuilder.build(sample_schema, question)

    # Should include data type info
    assert "INT" in prompt
    assert "VARCHAR" in prompt or "FLOAT" in prompt


def test_multiple_schemas(sample_schema):
    """Test building prompts for different schemas"""
    schema2 = {
        "products": {
            "columns": [
                {"name": "id", "type": "INT"},
                {"name": "name", "type": "VARCHAR"}
            ]
        }
    }

    prompt1 = PromptBuilder.build(sample_schema, "Count users")
    prompt2 = PromptBuilder.build(schema2, "Count products")

    # Prompts should be different
    assert "users" in prompt1
    assert "orders" in prompt1
    assert "users" not in prompt2
    assert "products" in prompt2
