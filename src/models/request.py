from typing import Optional

from pydantic import BaseModel, HttpUrl, field_validator


class BaseRequest(BaseModel):
    user_preference: Optional[str] = None

    @field_validator("user_preference")
    @classmethod
    def _strip_preference(cls, value: Optional[str]) -> Optional[str]:
        return value.strip() if isinstance(value, str) else value


class ImagePipelineRequest(BaseRequest):
    image_url: HttpUrl


class CardGenerationRequest(ImagePipelineRequest):
    central_object: Optional[str] = None


class ChatRequest(BaseRequest):
    card_context: str
    question: str
    conversation_id: Optional[str] = None
