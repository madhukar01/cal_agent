from fastapi import FastAPI

from rest_server.api.chat import router as chat_api_router


def import_routes(app: FastAPI) -> None:
    """
    Import routes from different modules and add them to the main application

    Args:
        app: FastAPI application
    """
    app.include_router(chat_api_router)
