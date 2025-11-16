import asyncio
import logging
from functools import lru_cache
from typing import Any, Dict, Optional

from src.clients.dify_client import (
    CardGenerationResult,
    DifyCardGenerationClient,
    DifyPreprocessingClient,
)
from src.clients.elevenlabs_client import ElevenLabsClient
from src.clients.gemini_client import GeminiClient
from src.nodes.image_highlighten import PROMPT as HIGHLIGHT_PROMPT
from src.services.storage import ImageUploadService, get_image_upload_service
from src.utils.errors import AppException, ErrorCode, ExternalServiceError
from src.utils.logger import get_logger


class PipelineService:
    def __init__(
        self,
        *,
        preprocess_client: DifyPreprocessingClient,
        card_client: DifyCardGenerationClient,
        gemini_client: GeminiClient,
        elevenlabs_client: ElevenLabsClient,
        storage_service: ImageUploadService,
        logger: logging.Logger,
    ):
        self.preprocess_client = preprocess_client
        self.card_client = card_client
        self.gemini_client = gemini_client
        self.elevenlabs_client = elevenlabs_client
        self.storage_service = storage_service
        self.logger = logger

    async def generate_card(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        image_url = payload["image_url"]
        user_preference = payload.get("user_preference")
        user_id = payload.get("user_id", "snapopedia")

        preprocess = await self.preprocess_client.analyze(
            image_url=image_url,
            user_preference=user_preference,
            user_id=user_id,
        )
        if preprocess.image_status != "clear" or not preprocess.central_object:
            raise AppException(
                error_code=ErrorCode.VALIDATION_ERROR,
                message="图片不够清晰或与主题不符，请重新拍摄",
            )

        highlight_task = asyncio.create_task(
            self._generate_highlight(image_url=image_url, central_object=preprocess.central_object)
        )
        card_result = await self.card_client.generate_card(
            image_url=image_url,
            central_object=preprocess.central_object,
            user_preference=user_preference,
            user_id=user_id,
        )
        highlighted_url = await highlight_task

        audio_url = await self._generate_audio(card_result)

        return {
            "title": card_result.title,
            "desc": card_result.desc,
            "central_object": preprocess.central_object,
            "highlighted_image_url": highlighted_url,
            "audio_url": audio_url,
        }

    async def _generate_highlight(self, *, image_url: str, central_object: str) -> Optional[str]:
        prompt = f"{HIGHLIGHT_PROMPT.strip()}\n中心物体：{central_object}"
        try:
            image_bytes = await self.gemini_client.highlight_object(image_url=image_url, prompt=prompt)
            return await self.storage_service.upload_highlight_image(image_bytes)
        except ExternalServiceError as exc:
            self.logger.warning("高亮图生成失败: %s", exc)
            return None
        except AppException as exc:
            self.logger.warning("高亮图上传失败: %s", exc)
            return None

    async def _generate_audio(self, card_result: CardGenerationResult) -> Optional[str]:
        text = f"{card_result.title}。{card_result.desc}"
        try:
            audio_bytes = await self.elevenlabs_client.synthesize_speech(text=text)
            return await self.storage_service.upload_audio(audio_bytes)
        except ExternalServiceError as exc:
            self.logger.warning("语音生成失败: %s", exc)
            return None
        except AppException as exc:
            self.logger.warning("语音上传失败: %s", exc)
            return None


@lru_cache(maxsize=1)
def get_pipeline_service() -> PipelineService:
    from src.clients.dify_client import get_dify_card_generation_client, get_dify_preprocessing_client
    from src.clients.elevenlabs_client import get_elevenlabs_client
    from src.clients.gemini_client import get_gemini_client

    return PipelineService(
        preprocess_client=get_dify_preprocessing_client(),
        card_client=get_dify_card_generation_client(),
        gemini_client=get_gemini_client(),
        elevenlabs_client=get_elevenlabs_client(),
        storage_service=get_image_upload_service(),
        logger=get_logger("PipelineService"),
    )
