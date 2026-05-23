"""SQL execution engine for running queries against SQLite database"""

import sqlite3
import logging
from typing import Any, List, Dict, Optional, Tuple
import json

logger = logging.getLogger(__name__)


class ExecutionEngine:
    """Execute SQL queries against a database"""

    def __init__(self, db_path: str = ":memory:"):
        """
        Initialize execution engine.

        Args:
            db_path: SQLite database path (':memory:' for in-memory)
        """
        self.db_path = db_path
        self.connection = None
        logger.info(f"ExecutionEngine initialized with db: {db_path}")

    def connect(self) -> bool:
        """
        Connect to database.

        Returns:
            True if successful
        """
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            logger.info(f"Connected to database: {self.db_path}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Connection error: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from database"""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("Disconnected from database")

    def execute(self, sql: str) -> Tuple[bool, Any, Optional[str]]:
        """
        Execute SQL query.

        Args:
            sql: SQL query string

        Returns:
            Tuple of (success, result, error)
            - success: bool indicating if execution succeeded
            - result: Query result (list of dicts) or affected rows count
            - error: Error message if failed
        """
        if not self.connection:
            return False, None, "Database not connected"

        if not sql or not sql.strip():
            return False, None, "SQL query cannot be empty"

        try:
            cursor = self.connection.cursor()
            cursor.execute(sql)

            # For SELECT queries, fetch results
            if sql.strip().upper().startswith("SELECT"):
                rows = cursor.fetchall()
                # Convert rows to list of dicts
                results = [dict(row) for row in rows]
                logger.info(f"Query executed successfully, returned {len(results)} rows")
                return True, results, None
            else:
                # For other queries, return affected rows count
                self.connection.commit()
                logger.info(f"Query executed, {cursor.rowcount} rows affected")
                return True, cursor.rowcount, None

        except sqlite3.Error as e:
            logger.error(f"SQL execution error: {e}")
            return False, None, str(e)
        except Exception as e:
            logger.error(f"Unexpected execution error: {e}")
            return False, None, f"Unexpected error: {str(e)}"

    def load_schema(self, schema_sql: str) -> Tuple[bool, Optional[str]]:
        """
        Load schema into database.

        Args:
            schema_sql: SQL CREATE TABLE statements

        Returns:
            Tuple of (success, error_message)
        """
        if not self.connection:
            return False, "Database not connected"

        try:
            cursor = self.connection.cursor()
            # Split by semicolon and execute each statement
            statements = [s.strip() for s in schema_sql.split(";") if s.strip()]

            for stmt in statements:
                cursor.execute(stmt)

            self.connection.commit()
            logger.info(f"Loaded schema with {len(statements)} statements")
            return True, None

        except sqlite3.Error as e:
            logger.error(f"Schema load error: {e}")
            return False, str(e)
        except Exception as e:
            logger.error(f"Unexpected schema load error: {e}")
            return False, str(e)

    def insert_sample_data(self, table: str, columns: List[str], rows: List[List[Any]]) -> Tuple[bool, Optional[str]]:
        """
        Insert sample data into table.

        Args:
            table: Table name
            columns: List of column names
            rows: List of rows (each row is list of values)

        Returns:
            Tuple of (success, error_message)
        """
        if not self.connection:
            return False, "Database not connected"

        try:
            cursor = self.connection.cursor()
            placeholders = ", ".join(["?" for _ in columns])
            col_names = ", ".join(columns)
            sql = f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})"

            cursor.executemany(sql, rows)
            self.connection.commit()

            logger.info(f"Inserted {cursor.rowcount} rows into {table}")
            return True, None

        except sqlite3.Error as e:
            logger.error(f"Data insertion error: {e}")
            return False, str(e)
        except Exception as e:
            logger.error(f"Unexpected insertion error: {e}")
            return False, str(e)

    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        Get information about a table.

        Args:
            table_name: Name of table

        Returns:
            Dictionary with table info
        """
        if not self.connection:
            return {}

        try:
            cursor = self.connection.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()

            table_info = {
                "name": table_name,
                "columns": []
            }

            for col in columns:
                table_info["columns"].append({
                    "name": col[1],
                    "type": col[2],
                    "notnull": bool(col[3]),
                    "default": col[4],
                    "pk": bool(col[5])
                })

            return table_info

        except sqlite3.Error as e:
            logger.error(f"Error getting table info: {e}")
            return {}

    def format_result(self, result: Any, max_rows: int = 1000) -> str:
        """
        Format query result as JSON string.

        Args:
            result: Query result
            max_rows: Maximum rows to include

        Returns:
            JSON string representation
        """
        if isinstance(result, list):
            # Convert to list of dicts, limit rows
            limited = result[:max_rows]
            return json.dumps(limited, indent=2, default=str)
        else:
            return json.dumps({"rows_affected": result}, indent=2)

    def execute_and_format(self, sql: str, format_json: bool = True) -> Dict[str, Any]:
        """
        Execute SQL and format result.

        Args:
            sql: SQL query
            format_json: Whether to format result as JSON

        Returns:
            Dictionary with execution result
        """
        success, result, error = self.execute(sql)

        return {
            "success": success,
            "result": result,
            "result_json": self.format_result(result) if success and format_json else None,
            "error": error,
            "row_count": len(result) if isinstance(result, list) else (result if isinstance(result, int) else 0)
        }

    def get_all_tables(self) -> List[str]:
        """Get list of all tables in database"""
        if not self.connection:
            return []

        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error listing tables: {e}")
            return []

    def __enter__(self):
        """Context manager support"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager support"""
        self.disconnect()
