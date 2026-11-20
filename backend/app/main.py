"""FastAPI application entrypoint for LearningBridge.

Configures request tracing, CORS, standard error envelopes, and health checks.
"""

from contextlib import asynccontextmanager
import time
import uuid
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api import api_router
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.exceptions import AppException
from app.core.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown hooks."""
    logger.info("Initializing LearningBridge backend services...")
    # Health verify DB connection on startup
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        logger.info("Database connectivity verified successfully.")
    except Exception as exc:
        logger.error(f"Initial database healthcheck failed: {exc}")

    yield

    logger.info("Shutting down LearningBridge backend services...")


app = FastAPI(
    title=settings.APP_NAME,
    description="Traceable diagnostic assessment, evidence-based intervention, and reassessment platform.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_tracing_middleware(request: Request, call_next):
    """Enriches each HTTP interaction with a unique request ID and logs duration."""
    req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    start_time = time.perf_counter()

    # Pass request ID down
    request.state.request_id = req_id

    response = await call_next(request)

    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
    response.headers["X-Request-ID"] = req_id
    response.headers["X-Response-Time-Ms"] = str(duration_ms)

    # Don't clutter logs with periodic health check polls
    if not request.url.path.startswith("/health"):
        logger.info(
            f"{request.method} {request.url.path} returned {response.status_code} in {duration_ms}ms",
            extra={"request_id": req_id},
        )

    return response


# Standard Error Envelope Exception Handlers (Section 7.2)
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    req_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "message": exc.message,
            "request_id": req_id,
            "details": exc.details,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    req_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "code": "VALIDATION_FAILED",
            "message": "Input data failed schema or format validation.",
            "request_id": req_id,
            "details": {"errors": exc.errors()},
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    req_id = getattr(request.state, "request_id", None)
    logger.error(
        f"Unhandled exception during {request.method} {request.url.path}: {exc}",
        exc_info=True,
        extra={"request_id": req_id},
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected server error occurred. Please contact the administrator.",
            "request_id": req_id,
            "details": {},
        },
    )


# Health & Readiness Probes (Section 8.1 - item 5)
@app.get("/health/live", tags=["Health & Diagnostics"])
def liveness_check():
    """Liveness probe: verifies process is alive and responsive."""
    return {"status": "alive", "service": "learningbridge-backend"}


@app.get("/health/ready", tags=["Health & Diagnostics"])
def readiness_check():
    """Readiness probe: validates database connectivity before receiving traffic."""
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as exc:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unready", "database": "unavailable", "reason": str(exc)},
        )


@app.get("/health/system", tags=["Health & Diagnostics"])
def system_diagnostics():
    """Operational visibility endpoint reporting queue, DB, and outbox metrics per Section 13.3."""
    t0 = time.perf_counter()
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
            db_latency_ms = round((time.perf_counter() - t0) * 1000, 2)

            from app.modules.jobs.models import Job, OutboxEvent
            job_counts = {
                "queued": db.query(Job).filter(Job.status == "queued").count(),
                "running": db.query(Job).filter(Job.status == "running").count(),
                "succeeded": db.query(Job).filter(Job.status == "succeeded").count(),
                "failed": db.query(Job).filter(Job.status == "failed").count(),
                "retry_pending": db.query(Job).filter(Job.status == "retry_pending").count(),
            }
            outbox_counts = {
                "pending": db.query(OutboxEvent).filter(OutboxEvent.status == "pending").count(),
                "dispatched": db.query(OutboxEvent).filter(OutboxEvent.status == "dispatched").count(),
            }

        return {
            "status": "healthy",
            "environment": settings.APP_ENV,
            "database": {
                "status": "connected",
                "ping_latency_ms": db_latency_ms,
            },
            "job_queue": job_counts,
            "outbox": outbox_counts,
        }
    except Exception as exc:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "degraded", "error": str(exc)},
        )


# Mount Versioned API Routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
