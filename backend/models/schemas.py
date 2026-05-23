"""Pydantic models for API requests and responses"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class ColumnSchema(BaseModel):
    """Database column definition"""
    name: str = Field(..., description="Column name")
    type: str = Field(..., description="Column data type (INT, VARCHAR, etc)")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "id",
                "type": "INT"
            }
        }


class TableSchema(BaseModel):
    """Database table definition"""
    name: str = Field(..., description="Table name")
    columns: List[ColumnSchema] = Field(..., description="List of columns")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "users",
                "columns": [
                    {"name": "id", "type": "INT"},
                    {"name": "email", "type": "VARCHAR"}
                ]
            }
        }


class SchemaUploadResponse(BaseModel):
    """Response after uploading a schema"""
    session_id: str = Field(..., description="Unique session ID for this upload")
    tables: List[TableSchema] = Field(..., description="Parsed database tables")
    table_count: int = Field(..., description="Number of tables parsed")
    message: str = Field(default="Schema uploaded successfully")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "abc123xyz",
                "tables": [
                    {
                        "name": "users",
                        "columns": [
                            {"name": "id", "type": "INT"},
                            {"name": "email", "type": "VARCHAR"}
                        ]
                    }
                ],
                "table_count": 1,
                "message": "Schema uploaded successfully"
            }
        }


class QueryRequest(BaseModel):
    """Request to generate SQL from natural language"""
    session_id: str = Field(..., description="Session ID from schema upload")
    question: str = Field(..., description="Natural language question")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "abc123xyz",
                "question": "What is the average age of users?"
            }
        }


class QueryResponse(BaseModel):
    """Response with generated SQL and results"""
    session_id: str
    generated_sql: str = Field(..., description="Generated SQL query")
    result: Optional[Any] = Field(default=None, description="Query execution result")
    error: Optional[str] = Field(default=None, description="Error message if query failed")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "abc123xyz",
                "generated_sql": "SELECT AVG(age) FROM users;",
                "result": 32.4,
                "error": None
            }
        }


class SessionInfo(BaseModel):
    """Session information"""
    session_id: str
    tables: List[TableSchema]
    created_at: str
    expires_at: str

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "abc123xyz",
                "tables": [],
                "created_at": "2026-05-23T12:00:00Z",
                "expires_at": "2026-05-23T12:15:00Z"
            }
        }
