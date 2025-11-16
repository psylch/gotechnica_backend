from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, HttpUrl


class BaseResponse(BaseModel):
    success: bool = True


class HealthResponse(BaseResponse):
    message: str = "OK"
    data: Dict[str, Any] = Field(default_factory=dict)


class ImageUploadResponse(BaseResponse):
    url: HttpUrl


class CardGenerationResponse(BaseResponse):
    title: str
    desc: str
    central_object: Optional[str] = None
    highlighted_image_url: Optional[str] = None
    audio_url: Optional[str] = None


class ChatResponse(BaseResponse):
    answer: str
    conversation_id: Optional[str] = None
    audio_url: Optional[str] = None
