from http import HTTPStatus

from fastapi import APIRouter

from src.models.request import ChatRequest
from src.models.response import ChatResponse
from src.utils.errors import AppException, ErrorCode

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse, status_code=HTTPStatus.NOT_IMPLEMENTED)
async def chat(request: ChatRequest) -> ChatResponse:  # pragma: no cover - placeholder
    del request
    raise AppException(
        error_code=ErrorCode.NOT_IMPLEMENTED,
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        message="问答接口将在 Phase 5 完成后开放",
    )
