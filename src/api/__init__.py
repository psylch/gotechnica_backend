from fastapi import APIRouter

from .cards import router as cards_router
from .chat import router as chat_router
from .images import router as images_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(images_router)
api_router.include_router(cards_router)
api_router.include_router(chat_router)
