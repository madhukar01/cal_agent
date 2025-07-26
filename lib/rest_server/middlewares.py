import uuid

import structlog
from fastapi import Request, Response
from starlette.middleware.base import RequestResponseEndpoint

from lib.rest_server.context import Context


async def create_context(
    request: Request,
    call_next: RequestResponseEndpoint,
) -> Response:
    """
    Create server context and bind it to the request.
    Also bind request context variables to the logger.

    Args:
        request: FastAPI request object
        call_next: Next middleware in chain

    Returns:
        Response: FastAPI response object
    """
    # Generate request ID
    request_id = uuid.uuid4().hex

    # Create context
    # pg_connection is kept null by default
    # individual request should acquire a connection from the pool
    # and bind it to the context whenever required
    server_context = Context(logger=request.app.logger, request_id=request_id)

    # Bind vars to structlog logger
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        url=str(request.url),
        method=request.method,
        request_id=request_id,
        client_host=request.client.host if request.client else None,
    )

    # Bind context to request state
    request.state.context = server_context

    # Process API call
    return await call_next(request)
