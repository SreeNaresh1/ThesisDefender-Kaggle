from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from api.routes import analyze, health
from config import settings
from services.model_client import create_model_client
from jobs.queue import JobQueue
from security.guards import audit_secrets

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    # Layer 3 — Secrets Management Audit
    # Log any secrets issues at startup without blocking the server.
    _secret_issues = audit_secrets()
    for _issue in _secret_issues:
        import logging as _logging
        _logging.getLogger(__name__).warning("[Security] Secrets audit: %s", _issue)

    app.state.model_client = create_model_client()
    app.state.job_queue = JobQueue(settings.REDIS_URL)
    await app.state.job_queue.connect()
    
    yield
    
    # Shutdown
    await app.state.job_queue.close()

app = FastAPI(
    title="ThesisDefender",
    description="Adversarial argument reasoning agent API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(analyze.router, prefix="/api/analyze", tags=["analyze"])

from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={"Access-Control-Allow-Origin": "*"}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "detail": str(exc)},
        headers={"Access-Control-Allow-Origin": "*"}
    )
