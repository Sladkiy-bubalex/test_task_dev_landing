from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from contextlib import asynccontextmanager

from .config import settings
from app.api.routes import contact, health, metrics
from app.middleware.error_handler import global_exception_handler
from app.middleware.logging import setup_logging, LoggingMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    setup_logging()
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")

    yield

    # Shutdown
    logger.info("Shutting down application")
    logger.info("Cleaning up resources...")


app = FastAPI(
    title="Developer Landing API",
    description="Backend API for developer landing page with AI integration",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging middleware
app.add_middleware(LoggingMiddleware)

# Exception handlers
app.add_exception_handler(Exception, global_exception_handler)

# Include routers
app.include_router(contact.router, prefix="/api", tags=["Contact"])
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(metrics.router, prefix="/api", tags=["Metrics"])


# Root endpoint
@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/api/health",
    }
