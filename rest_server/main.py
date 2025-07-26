from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from lib.core.logger import initialize_logger
from lib.rest_server.middlewares import create_context
from rest_server.import_routes import import_routes


class CustomFastAPI(FastAPI):
    """Extended FastAPI class with custom attributes"""

    logger: structlog.BoundLogger


@asynccontextmanager
async def lifespan(app: CustomFastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan context manager for FastAPI application.
    Handles startup and shutdown events.

    Args:
        app: CustomFastAPI application
    """
    # Startup

    # Initialize logger
    initialize_logger("rest_server")
    app.logger = structlog.get_logger("rest_server")
    await app.logger.info("Server starting up")

    # Import routers
    import_routes(app)

    yield  # Server is running

    # Shutdown
    await app.logger.info("Server shutting down")


# Create fastAPI app
server = CustomFastAPI(lifespan=lifespan)

# Add middlewares
origins = ["*"]
server.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add context middleware
server.add_middleware(BaseHTTPMiddleware, dispatch=create_context)


@server.exception_handler(Exception)  # type: ignore[misc]
async def general_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Handle unhandled exceptions globally

    Args:
        request: FastAPI request object
        exc: Unhandled exception

    Returns:
        JSONResponse: Internal server error response
    """
    # Log the error
    request.state.context.logger.error(
        "Unhandled exception",
        exc_info=exc,
    )
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"},
    )
