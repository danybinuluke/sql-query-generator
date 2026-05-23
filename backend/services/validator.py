"""SQL validator to ensure safe query execution"""

import logging
import re
from typing import Tuple

logger = logging.getLogger(__name__)


class SQLValidator:
    """Validate SQL queries for safety before execution"""

    # Dangerous SQL keywords that should be blocked
    DANGEROUS_KEYWORDS = {
        "DROP", "DELETE", "TRUNCATE", "ALTER", "GRANT", "REVOKE",
        "CREATE", "INSERT", "UPDATE", "REPLACE", "ATTACH",
        "DETACH", "PRAGMA", "VACUUM", "REINDEX"
    }

    # Safe keywords (allowed in SELECT queries)
    SAFE_KEYWORDS = {
        "SELECT", "FROM", "WHERE", "GROUP", "ORDER", "BY",
        "HAVING", "LIMIT", "OFFSET", "DISTINCT", "AND", "OR",
        "NOT", "IN", "LIKE", "BETWEEN", "IS", "NULL", "JOIN",
        "INNER", "LEFT", "RIGHT", "FULL", "OUTER", "CROSS", "ON",
        "UNION", "INTERSECT", "EXCEPT", "CASE", "WHEN", "THEN",
        "ELSE", "END", "AS", "WITH", "CTE", "RECURSIVE"
    }

    # Aggregate functions (allowed)
    AGGREGATE_FUNCTIONS = {
        "COUNT", "SUM", "AVG", "MIN", "MAX", "GROUP_CONCAT",
        "STDDEV", "VARIANCE"
    }

    @staticmethod
    def validate(sql: str) -> Tuple[bool, str]:
        """
        Validate SQL query for safety.

        Args:
            sql: SQL query string

        Returns:
            Tuple of (is_valid, message)
        """
        if not sql or not sql.strip():
            return False, "SQL query cannot be empty"

        try:
            sql = sql.strip()

            # Check for null bytes and other suspicious characters
            if '\x00' in sql or '\r' in sql:
                return False, "SQL contains suspicious characters"

            # Check first keyword
            first_keyword = SQLValidator._get_first_keyword(sql)

            if not first_keyword:
                return False, "Could not determine query type"

            if first_keyword not in ("SELECT", "WITH"):
                return False, f"Only SELECT queries allowed, got: {first_keyword}"

            # Check for dangerous keywords
            dangerous_found = SQLValidator._check_dangerous_keywords(sql)
            if dangerous_found:
                return False, f"Query contains forbidden keyword: {dangerous_found}"

            # Check comment injection
            if SQLValidator._has_comment_injection(sql):
                return False, "SQL contains suspicious comment patterns"

            # Check for semicolon at end (except trailing whitespace)
            if sql.rstrip().endswith(";"):
                # Allow it, but clean it up
                sql = sql.rstrip()
                if sql.endswith(";"):
                    # OK to end with semicolon
                    pass

            logger.info(f"SQL validation passed for {len(sql)} char query")
            return True, "SQL is valid and safe"

        except Exception as e:
            logger.error(f"Error during SQL validation: {e}")
            return False, f"Validation error: {str(e)}"

    @staticmethod
    def _get_first_keyword(sql: str) -> str:
        """Extract first SQL keyword from query"""
        # Remove leading whitespace and comments
        sql = sql.strip()

        # Remove line comments
        if sql.startswith("--"):
            first_line = sql.split("\n")[0][2:].strip()
            sql = "\n".join(sql.split("\n")[1:])

        # Remove block comments
        if sql.startswith("/*"):
            end = sql.find("*/")
            if end != -1:
                sql = sql[end + 2:].strip()

        # Extract first word
        match = re.match(r"^([A-Z_]+)", sql.upper())
        return match.group(1) if match else ""

    @staticmethod
    def _check_dangerous_keywords(sql: str) -> str:
        """
        Check if SQL contains dangerous keywords.

        Args:
            sql: SQL query string

        Returns:
            First dangerous keyword found, or empty string if none
        """
        sql_upper = sql.upper()

        # Remove string literals to avoid false positives
        sql_clean = SQLValidator._remove_string_literals(sql_upper)

        for keyword in SQLValidator.DANGEROUS_KEYWORDS:
            # Use word boundary regex to match whole keywords
            pattern = rf"\b{keyword}\b"
            if re.search(pattern, sql_clean):
                logger.warning(f"Dangerous keyword found: {keyword}")
                return keyword

        return ""

    @staticmethod
    def _has_comment_injection(sql: str) -> bool:
        """
        Check for comment injection attempts.

        Args:
            sql: SQL query string

        Returns:
            True if suspicious comment patterns found
        """
        # Check for multiple comment markers in sequence
        if sql.count("--") > 3:
            return True

        if sql.count("/*") > 2:
            return True

        # Check for comment markers after data
        if re.search(r"'\s*(--|/\*)", sql):
            return True

        return False

    @staticmethod
    def _remove_string_literals(sql: str) -> str:
        """
        Remove string literals from SQL to avoid false positives.

        Args:
            sql: SQL query string

        Returns:
            SQL with string literals replaced with spaces
        """
        # Replace single-quoted strings
        sql = re.sub(r"'([^']*)'", " ", sql)

        # Replace double-quoted strings
        sql = re.sub(r'"([^"]*)"', " ", sql)

        # Replace backtick-quoted identifiers
        sql = re.sub(r"`([^`]*)`", " ", sql)

        return sql

    @staticmethod
    def is_select_query(sql: str) -> bool:
        """Check if query is a SELECT query"""
        first_keyword = SQLValidator._get_first_keyword(sql)
        return first_keyword in ("SELECT", "WITH")

    @staticmethod
    def extract_tables(sql: str) -> list:
        """
        Extract table names from SQL query.

        Args:
            sql: SQL query string

        Returns:
            List of table names
        """
        # Simple regex to find table names after FROM and JOIN
        tables = []

        # Pattern: FROM tablename or JOIN tablename
        pattern = r"\b(?:FROM|JOIN)\s+(?:(?:LEFT|RIGHT|INNER|OUTER|FULL)\s+)*(?:JOIN\s+)?(?:`|\")?(\w+)(?:`|\")?"

        matches = re.finditer(pattern, sql, re.IGNORECASE)
        for match in matches:
            table_name = match.group(1)
            if table_name.upper() not in SQLValidator.DANGEROUS_KEYWORDS:
                tables.append(table_name)

        return list(set(tables))  # Remove duplicates

    @staticmethod
    def get_validation_report(sql: str) -> dict:
        """
        Get detailed validation report for SQL.

        Args:
            sql: SQL query string

        Returns:
            Dictionary with validation details
        """
        is_valid, message = SQLValidator.validate(sql)

        return {
            "is_valid": is_valid,
            "message": message,
            "is_select": SQLValidator.is_select_query(sql),
            "tables": SQLValidator.extract_tables(sql),
            "length": len(sql),
        }
