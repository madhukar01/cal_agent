from uuid import uuid4

from fastapi import APIRouter, Request

from lib.core.chat_agent import ChatAgent
from rest_server.api.chat.models import ChatRequest, ChatResponse

router = APIRouter()


def get_chat_agent(request: Request) -> ChatAgent:
    """
    Dependency injector to get the ChatAgent instance from the request context.
    """
    return request.state.context.chat_agent


@router.post("/message", response_model=ChatResponse)
async def post_message(request: Request, data: ChatRequest) -> ChatResponse:
    """
    Handles a chat request by invoking the ChatAgent.
    """
    context = request.state.context
    session_id = data.session_id or uuid4()
    response_text = await context.chat_agent.get_response(
        session_id=str(session_id), message=data.message, logger=context.logger
    )
    return ChatResponse(response=response_text, session_id=session_id)
