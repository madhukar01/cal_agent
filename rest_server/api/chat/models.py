from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str
    session_id: UUID | None = None
    metadata: dict | None = None


class ChatResponse(BaseModel):
    response: str
    session_id: UUID = Field(default_factory=uuid4)
    metadata: dict | None = None
