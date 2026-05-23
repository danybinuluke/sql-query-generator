"""SQLGenie FastAPI Application"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging

from backend.services import SchemaParser, SessionStore
from backend.models import SchemaUploadResponse, TableSchema, ColumnSchema

logger = logging.getLogger(__name__)

# Global session store
_session_store: SessionStore = None


def get_session_store() -> SessionStore:
    """Get or create session store instance"""
    global _session_store
    if _session_store is None:
        timeout_minutes = int(os.getenv("SESSION_TIMEOUT_MINUTES", 15))
        _session_store = SessionStore(timeout_minutes=timeout_minutes)
    return _session_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("🚀 SQLGenie Backend Starting...")
    # Initialize session store
    get_session_store()
    yield
    logger.info("🛑 SQLGenie Backend Shutting Down...")


app = FastAPI(
    title="SQLGenie API",
    description="AI SQL Assistant - Convert natural language to SQL",
    version="0.1.0",
    lifespan=lifespan
)

# CORS Configuration
allowed_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:8000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> dict:
    """
    Health check endpoint.

    Used by load balancers and monitoring systems to verify
    the service is running and responsive.

    Returns:
        dict: {"status": "ok"}
    """
    return {"status": "ok"}


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "SQLGenie API",
        "version": "0.1.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "openapi": "/openapi.json"
        }
    }


@app.get("/info")
async def info():
    """Get API information"""
    return {
        "name": "SQLGenie",
        "description": "AI SQL Assistant",
        "version": "0.1.0",
        "environment": os.getenv("ENV", "development"),
        "debug": os.getenv("DEBUG", "False") == "True"
    }


@app.post("/upload-schema", response_model=SchemaUploadResponse)
async def upload_schema(file: UploadFile = File(...)) -> SchemaUploadResponse:
    """
    Upload and parse SQL schema file.

    Accepts a .sql file, extracts CREATE TABLE statements,
    parses table and column information, and returns a session ID
    for subsequent queries.

    Args:
        file: SQL file upload

    Returns:
        SchemaUploadResponse: Session ID and parsed schema

    Raises:
        HTTPException: If file is invalid or parsing fails
    """
    # Validate file type
    if not file.filename.endswith(".sql"):
        raise HTTPException(
            status_code=400,
            detail="File must be a .sql file"
        )

    # Read file content
    try:
        content = await file.read()
        schema_text = content.decode("utf-8")
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Error reading file: {str(e)}"
        )

    # Parse schema
    try:
        parser = SchemaParser()
        parsed_schema = parser.parse(schema_text)
    except ValueError as e:
        logger.error(f"Schema parsing error: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Schema parsing error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error parsing schema: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal error parsing schema"
        )

    # Create session
    try:
        session_store = get_session_store()
        session_id = session_store.create_session(parsed_schema)
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error creating session"
        )

    # Convert to response model
    tables = [
        TableSchema(
            name=table_name,
            columns=[
                ColumnSchema(name=col["name"], type=col["type"])
                for col in table_info["columns"]
            ]
        )
        for table_name, table_info in parsed_schema.items()
    ]

    logger.info(f"Schema uploaded: session={session_id}, tables={len(tables)}")

    return SchemaUploadResponse(
        session_id=session_id,
        tables=tables,
        table_count=len(tables),
        message="Schema uploaded successfully"
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        log_level="info"
    )
