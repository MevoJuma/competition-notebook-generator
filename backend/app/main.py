from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import settings
from app.core.database import init_db
from app.core.exceptions import CompetitionPlatformException
from app.core.logging import get_logger, setup_logging

setup_logging()
logger = get_logger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager: runs startup and shutdown hooks."""
    logger.info("Starting up %s v%s", settings.PROJECT_NAME, settings.VERSION)
    await init_db()
    logger.info("Storage uploads directory: %s", settings.upload_path)
    logger.info("Storage generated directory: %s", settings.generated_path)
    yield
    logger.info("Shutting down %s", settings.PROJECT_NAME)


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Automated AI competition analysis, data profiling, and high-performance notebook generator.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.exception_handler(CompetitionPlatformException)
async def domain_exception_handler(request: Request, exc: CompetitionPlatformException) -> JSONResponse:
    """Handle known domain exceptions cleanly with their designated status codes."""
    logger.warning("Domain exception caught on %s %s: %s", request.method, request.url.path, exc.message)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.message,
            "details": exc.details,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Fallback handler for unhandled server exceptions."""
    logger.error("Unhandled exception caught on %s %s", request.method, request.url.path, exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "message": "An unexpected internal server error occurred.",
            "details": {"error_type": exc.__class__.__name__},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


@app.get("/", tags=["Root"])
async def root():
    """Root platform metadata endpoint."""
    return {
        "platform": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "healthy",
        "docs_url": "/docs",
    }


@app.get("/api/health", tags=["Health"])
@app.get(f"{settings.API_V1_STR}/health", tags=["Health"])
async def health_check():
    """System health check and timestamp."""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "storage": {
            "upload_dir_exists": settings.upload_path.exists(),
            "generated_dir_exists": settings.generated_path.exists(),
        },
    }
