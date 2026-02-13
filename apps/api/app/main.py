"""pruv API — FastAPI application at api.pruv.dev."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .core.config import settings
from .routes import admin, analytics, auth, chains, checkpoints, receipts, verify, webhooks
from .schemas.schemas import HealthResponse

logger = logging.getLogger("pruv.api")

app = FastAPI(
    title="pruv API",
    description="Prove what happened. Cryptographic verification for any system.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — explicit methods and headers, no wildcards
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins or [
        "https://app.pruv.dev",
        "https://pruv.dev",
        "http://localhost:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Request-ID"],
)


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
