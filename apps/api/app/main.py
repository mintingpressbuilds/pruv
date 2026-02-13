"""pruv API — FastAPI application at api.pruv.dev."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .routes import admin, analytics, auth, chains, checkpoints, receipts, verify, webhooks
from .schemas.schemas import HealthResponse

app = FastAPI(
    title="pruv API",
    description="Prove what happened. Cryptographic verification for any system.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins or [
        "https://app.pruv.dev",
        "https://pruv.dev",
        "http://localhost:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
