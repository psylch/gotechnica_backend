from http import HTTPStatus

from fastapi import APIRouter, Depends

from src.models.request import ChatRequest
from src.models.response import ChatResponse
from src.services.chat import ChatService, get_chat_service

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse, status_code=HTTPStatus.OK)
async def chat(request: ChatRequest, service: ChatService = Depends(get_chat_service)) -> ChatResponse:
    result = await service.chat(
        question=request.question,
        card_context=request.card_context,
        user_id="snapopedia-chat",
        user_preference=request.user_preference,
        conversation_id=request.conversation_id,
        image_url=str(request.image_url) if request.image_url else None,
        need_audio=request.need_audio,
    )
    return ChatResponse(**result)
