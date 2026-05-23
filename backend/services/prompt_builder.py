"""Prompt builder for generating LLM prompts from schema and questions"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class PromptBuilder:
    """Build structured prompts for SQL generation"""

    SYSTEM_PROMPT = """You are an expert SQL assistant. Your task is to generate accurate, safe SQL queries based on natural language questions and database schemas.

CRITICAL RULES:
1. Generate ONLY SELECT statements (no INSERT, UPDATE, DELETE, DROP, ALTER, etc.)
2. Use ONLY tables and columns that exist in the schema
3. Return the SQL query with no explanation or markdown
4. Do NOT use any table aliases unless necessary
5. Use standard SQL syntax that works with most databases
6. If the question is ambiguous, make reasonable assumptions
7. Include GROUP BY for aggregate queries
8. For multiple joins, ensure proper ON conditions"""

    SCHEMA_INSTRUCTION = """Database Schema:
Below are the available tables and their columns. Only use these tables and columns in your query.

"""

    QUESTION_INSTRUCTION = """Question:
{question}

Generate the SQL query (SELECT statement only):"""

    @staticmethod
    def build(schema: Dict[str, Any], question: str) -> str:
        """
        Build a structured prompt for SQL generation.

        Args:
            schema: Parsed schema dict with tables and columns
            question: Natural language question from user

        Returns:
            Formatted prompt string for LLM
        """
        if not schema:
            logger.warning("Empty schema provided to prompt builder")
            raise ValueError("Schema cannot be empty")

        if not question or not question.strip():
            logger.warning("Empty question provided to prompt builder")
            raise ValueError("Question cannot be empty")

        logger.info(f"Building prompt for {len(schema)} tables")

        # Start with system prompt
        prompt = PromptBuilder.SYSTEM_PROMPT
        prompt += "\n\n" + PromptBuilder.SCHEMA_INSTRUCTION

        # Add schema information
        for table_name, table_info in schema.items():
            prompt += f"\nTable: {table_name}\n"
            prompt += "Columns:\n"

            columns = table_info.get("columns", [])
            if not columns:
                logger.warning(f"Table {table_name} has no columns")
                continue

            for col in columns:
                col_name = col.get("name", "unknown")
                col_type = col.get("type", "unknown")
                prompt += f"  - {col_name} ({col_type})\n"

        # Add question
        prompt += "\n" + PromptBuilder.QUESTION_INSTRUCTION.format(question=question)
        prompt += "\n"

        return prompt

    @staticmethod
    def build_with_examples(
        schema: Dict[str, Any],
        question: str,
        examples: List[Dict[str, str]] = None
    ) -> str:
        """
        Build a prompt with few-shot examples for better performance.

        Args:
            schema: Parsed schema dict
            question: User question
            examples: List of {"question": "...", "sql": "..."} dicts

        Returns:
            Formatted prompt with examples
        """
        # Start with base prompt
        prompt = PromptBuilder.build(schema, question)

        # Add examples if provided
        if examples:
            prompt = PromptBuilder.SYSTEM_PROMPT
            prompt += "\n\nEXAMPLES:\n"

            for i, example in enumerate(examples, 1):
                prompt += f"\nExample {i}:\n"
                prompt += f"Question: {example.get('question', '')}\n"
                prompt += f"SQL: {example.get('sql', '')}\n"

            prompt += "\n" + PromptBuilder.SCHEMA_INSTRUCTION

            # Add schema
            for table_name, table_info in schema.items():
                prompt += f"\nTable: {table_name}\n"
                prompt += "Columns:\n"
                for col in table_info.get("columns", []):
                    prompt += f"  - {col.get('name')} ({col.get('type')})\n"

            prompt += "\n" + PromptBuilder.QUESTION_INSTRUCTION.format(question=question)
            prompt += "\n"

        return prompt

    @staticmethod
    def validate_question(question: str) -> bool:
        """
        Validate that question is safe and appropriate.

        Args:
            question: User question

        Returns:
            True if question is valid
        """
        if not question or not question.strip():
            return False

        # Check length (reasonable bounds)
        if len(question) > 1000:
            return False

        # Check for dangerous keywords that should trigger warnings
        dangerous = ["drop", "delete", "truncate", "alter", "create", "insert", "update"]
        question_lower = question.lower()
        for keyword in dangerous:
            if keyword in question_lower:
                logger.warning(f"Question contains potentially dangerous keyword: {keyword}")

        return True

    @staticmethod
    def extract_sql_from_response(response_text: str) -> str:
        """
        Extract SQL from LLM response (may contain markdown/explanation).

        Args:
            response_text: Raw LLM response

        Returns:
            Extracted SQL statement
        """
        # Remove markdown code blocks if present
        if "```sql" in response_text:
            start = response_text.index("```sql") + 6
            end = response_text.index("```", start)
            return response_text[start:end].strip()
        elif "```" in response_text:
            start = response_text.index("```") + 3
            end = response_text.index("```", start)
            return response_text[start:end].strip()

        # Otherwise return as-is (assume it's already SQL)
        return response_text.strip()