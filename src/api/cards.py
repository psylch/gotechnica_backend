from http import HTTPStatus

from fastapi import APIRouter

from src.models.request import CardGenerationRequest
from src.models.response import CardGenerationResponse
from src.utils.errors import AppException, ErrorCode

router = APIRouter(prefix="/cards", tags=["cards"])


@router.post("/generate", response_model=CardGenerationResponse, status_code=HTTPStatus.NOT_IMPLEMENTED)
async def generate_card(request: CardGenerationRequest) -> CardGenerationResponse:  # pragma: no cover - placeholder
    del request
    raise AppException(
        error_code=ErrorCode.NOT_IMPLEMENTED,
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        message="卡片生成将在 Pipeline 实现后开放",
    )
