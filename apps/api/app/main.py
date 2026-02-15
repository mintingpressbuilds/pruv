"""pruv API — FastAPI application at api.pruv.dev."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .core.config import settings
from .middleware.cors import CORSConfig, SecurityHeadersMiddleware
from .middleware.logging import RequestLoggingMiddleware
from .models.database import Base, get_engine
from .routes import admin, analytics, auth, chains, checkpoints, dashboard, receipts, verify, webhooks
from .schemas.schemas import HealthResponse

logger = logging.getLogger("pruv.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup if they don't exist."""
    if settings.database_url:
        try:
            engine = get_engine(settings.database_url)
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables verified/created.")
        except Exception:
            logger.exception("Failed to create database tables.")
    yield


app = FastAPI(
    title="pruv API",
    description="Prove what happened. Cryptographic verification for any system.",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# CORS — environment-aware, no localhost in production
environment = os.getenv("PRUV_ENV", "development")
cors_config = CORSConfig(environment=environment)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins or cors_config.allow_origins,
    allow_credentials=cors_config.allow_credentials,
    allow_methods=cors_config.allow_methods,
    allow_headers=cors_config.allow_headers,
    expose_headers=cors_config.expose_headers,
    max_age=cors_config.max_age,
)

# Security headers — HSTS, CSP, X-Frame-Options, etc.
app.add_middleware(SecurityHeadersMiddleware)

# Request logging — structured log entries for every request
app.add_middleware(RequestLoggingMiddleware)


# Global exception handler — never leak stack traces
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# Routes
app.include_router(auth.router)
app.include_router(chains.router)
app.include_router(checkpoints.router)
app.include_router(dashboard.router)
app.include_router(receipts.router)
app.include_router(verify.router)
app.include_router(webhooks.router)
app.include_router(analytics.router)
app.include_router(admin.router)


@app.get("/", response_model=HealthResponse)
async def health():
    """Health check."""
    return {"status": "ok", "version": "1.0.0"}


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": "1.0.0"}
