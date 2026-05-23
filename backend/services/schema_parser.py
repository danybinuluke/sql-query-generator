"""SQL schema parser for extracting tables and columns from SQL DDL"""

import re
import logging
from typing import Dict, List, Any

import sqlparse

logger = logging.getLogger(__name__)


class SchemaParser:
    """Parse SQL CREATE TABLE statements to extract schema information"""

    # Supported SQL data types
    SUPPORTED_TYPES = {
        "INT", "INTEGER", "BIGINT", "SMALLINT", "TINYINT",
        "VARCHAR", "CHAR", "TEXT", "STRING",
        "DATE", "DATETIME", "TIMESTAMP",
        "FLOAT", "DOUBLE", "DECIMAL", "NUMERIC",
        "BOOLEAN", "BOOL",
        "JSON", "JSONB",
    }

    def parse(self, schema_text: str) -> Dict[str, Any]:
        """
        Parse SQL schema and extract table/column information.

        Args:
            schema_text: SQL DDL text with CREATE TABLE statements

        Returns:
            Dictionary mapping table names to their column definitions
            {
                "table_name": {
                    "columns": [
                        {"name": "id", "type": "INT"},
                        {"name": "email", "type": "VARCHAR"}
                    ]
                }
            }

        Raises:
            ValueError: If schema_text is empty or invalid
        """
        if not schema_text or not schema_text.strip():
            raise ValueError("Schema text cannot be empty")

        schema = {}
        statements = sqlparse.split(schema_text)

        for stmt in statements:
            stmt = stmt.strip()

            if not stmt or not stmt.upper().startswith("CREATE TABLE"):
                continue

            table_name = self._extract_table_name(stmt)
            if not table_name:
                logger.warning(f"Could not extract table name from: {stmt[:50]}...")
                continue

            columns = self._extract_columns(stmt)
            if not columns:
                logger.warning(f"No columns found in table {table_name}")
                continue

            schema[table_name] = {"columns": columns}
            logger.info(f"Parsed table {table_name} with {len(columns)} columns")

        if not schema:
            raise ValueError("No valid CREATE TABLE statements found in schema")

        logger.info(f"Successfully parsed {len(schema)} tables")
        return schema

    def _extract_table_name(self, statement: str) -> str:
        """Extract table name from CREATE TABLE statement"""
        match = re.search(
            r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[\"`]?(\w+)[\"`]?",
            statement,
            re.IGNORECASE
        )
        return match.group(1) if match else ""

    def _extract_columns(self, statement: str) -> List[Dict[str, str]]:
        """Extract column names and types from CREATE TABLE statement"""
        columns = []

        # Remove the CREATE TABLE ... ( part and keep content
        content_match = re.search(r"\((.*)\)", statement, re.DOTALL)
        if not content_match:
            return columns

        content = content_match.group(1)

        # Split by comma, but be careful with nested parentheses
        parts = self._smart_split(content, ",")

        for part in parts:
            part = part.strip()

            # Skip constraints, primary keys, foreign keys
            if any(x in part.upper() for x in ["PRIMARY KEY", "FOREIGN KEY", "CONSTRAINT", "CHECK", "DEFAULT", "NOT NULL", "UNIQUE"]):
                # Try to extract column name and type before the constraint
                col_match = re.match(r"(\w+)\s+(\w+)", part)
                if col_match:
                    col_name, col_type = col_match.groups()
                    if col_type.upper() in self.SUPPORTED_TYPES:
                        columns.append({
                            "name": col_name,
                            "type": col_type.upper()
                        })
                continue

            # Extract column name and type
            match = re.match(
                r"[\"`]?(\w+)[\"`]?\s+([A-Z]+(?:\([^)]*\))?)",
                part,
                re.IGNORECASE
            )

            if match:
                col_name, col_type = match.groups()
                # Extract base type (e.g., VARCHAR(100) -> VARCHAR)
                base_type = re.match(r"([A-Z]+)", col_type, re.IGNORECASE).group(1)

                if base_type.upper() in self.SUPPORTED_TYPES:
                    columns.append({
                        "name": col_name,
                        "type": base_type.upper()
                    })

        return columns

    @staticmethod
    def _smart_split(text: str, delimiter: str) -> List[str]:
        """Split text by delimiter, respecting parentheses"""
        parts = []
        current = []
        paren_count = 0

        for char in text:
            if char == "(":
                paren_count += 1
                current.append(char)
            elif char == ")":
                paren_count -= 1
                current.append(char)
            elif char == delimiter and paren_count == 0:
                parts.append("".join(current))
                current = []
            else:
                current.append(char)

        if current:
            parts.append("".join(current))

        return parts