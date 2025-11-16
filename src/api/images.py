from http import HTTPStatus

from fastapi import APIRouter, Depends, File, UploadFile

from src.models.response import ImageUploadResponse
from src.services.storage import ImageUploadService, get_image_upload_service

router = APIRouter(prefix="/images", tags=["images"])


def get_upload_service() -> ImageUploadService:
    return get_image_upload_service()


@router.post("/upload", response_model=ImageUploadResponse, status_code=HTTPStatus.CREATED)
async def upload_image(
    file: UploadFile = File(...),
    service: ImageUploadService = Depends(get_upload_service),
) -> ImageUploadResponse:
    url = await service.upload_original_image(file)
    return ImageUploadResponse(url=url)
