"""FastAPI application entry point."""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from nlap.api.dependencies import close_clients, initialize_clients
from nlap.api.routes import health, query
from nlap.config.settings import get_settings
from nlap.utils.logger import bind_request_context, clear_request_context, get_logger, setup_logging

# Initialize logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    logger.info("Starting NLAP application")
    settings = get_settings()
    logger.info(
        "Application configuration",
        app_name=settings.app.app_name,
        environment=settings.app.environment,
        debug=settings.app.debug,
    )

    try:
        await initialize_clients()
        logger.info("All clients initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize clients", error=str(e))
        raise

    yield

    # Shutdown
    logger.info("Shutting down NLAP application")
    await close_clients()
    logger.info("All clients closed")


# Create FastAPI application
settings = get_settings()
app = FastAPI(
    title="Natural Language Analytics Platform",
    description="Platform for natural language query processing and OpenSearch data extraction",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log request and response with structured logging."""
    import uuid

    request_id = str(uuid.uuid4())
    bind_request_context(request_id=request_id, path=request.url.path, method=request.method)

    start_time = time.time()

    logger.info(
        "Incoming request",
        method=request.method,
        path=request.url.path,
        query_params=dict(request.query_params),
    )

    try:
        response = await call_next(request)
        process_time = time.time() - start_time

        logger.info(
            "Request completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            process_time=process_time,
        )

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            "Request failed",
            method=request.method,
            path=request.url.path,
            error=str(e),
            error_type=type(e).__name__,
            process_time=process_time,
        )
        clear_request_context()
        raise
    finally:
        clear_request_context()


# Error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(
        "Unhandled exception",
        error=str(exc),
        error_type=type(exc).__name__,
        path=request.url.path,
    )

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "error": str(exc) if settings.app.debug else "An unexpected error occurred",
        },
    )


# Include routers
app.include_router(health.router)
app.include_router(query.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Natural Language Analytics Platform",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }

