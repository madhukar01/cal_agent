from dataclasses import dataclass

import structlog


@dataclass
class Context:
    """
    Context class represents essential connectors for each request.

    Attributes:
        logger: structlog logger
        request_id: string request ID
    """

    logger: structlog.stdlib.AsyncBoundLogger
    request_id: str
