from http import HTTPStatus

from fastapi import APIRouter, Depends

from src.models.request import CardGenerationRequest
from src.models.response import CardGenerationResponse
from src.services.pipeline import PipelineService, get_pipeline_service

router = APIRouter(prefix="/cards", tags=["cards"])


def get_service() -> PipelineService:
    return get_pipeline_service()


@router.post("/generate", response_model=CardGenerationResponse, status_code=HTTPStatus.OK)
async def generate_card(
    request: CardGenerationRequest,
    service: PipelineService = Depends(get_service),
) -> CardGenerationResponse:
    payload = request.model_dump(mode="json")
    result = await service.generate_card(payload)
    return CardGenerationResponse(**result)
