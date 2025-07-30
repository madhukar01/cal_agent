from fastapi import APIRouter

from .post_message import router as post_message_router

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])
router.include_router(post_message_router)
