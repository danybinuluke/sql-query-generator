"""SQLGenie FastAPI Application"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("🚀 SQLGenie Backend Starting...")
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        log_level="info"
    )
