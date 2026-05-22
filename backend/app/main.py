from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import QuBEException, qube_exception_handler
from app.core.logging import setup_logging, get_logger
from app.db.database import engine

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"🚀 QuBE Backend starting — {settings.environment} mode")
    yield
    await engine.dispose()
    logger.info("QuBE Backend shutting down")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
## QuBE - Quick Business Engine

AI-powered Natural Language to SQL business intelligence platform.

### Features
- 🤖 Natural language to SQL via OpenAI
- 📊 Auto-generated charts and KPI dashboards
- 🎫 Automatic ticket lifecycle management
- 📤 CSV and Excel export
- 🔒 JWT authentication

### Quick Start
1. Register at `POST /api/v1/auth/register`
2. Login at `POST /api/v1/auth/login` to get your token
3. Ask questions at `POST /api/v1/queries/ask`
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ─── CORS ─────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Exception Handlers ───────────────────────────────────────────────────────

@app.exception_handler(QuBEException)
async def handle_qube_exception(request: Request, exc: QuBEException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "error_type": type(exc).__name__},
    )


@app.exception_handler(Exception)
async def handle_generic_exception(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred", "error_type": "InternalServerError"},
    )

# ─── Routers ──────────────────────────────────────────────────────────────────

app.include_router(api_router)

# ─── Health Check ─────────────────────────────────────────────────────────────

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Welcome to QuBE — Quick Business Engine",
        "docs": "/docs",
        "version": settings.app_version,
    }
