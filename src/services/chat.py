from __future__ import annotations

from functools import lru_cache
from typing import Dict, Optional

from src.clients.dify_client import DifyQAClient, QAResult, get_dify_qa_client
from src.clients.elevenlabs_client import ElevenLabsClient, get_elevenlabs_client
from src.services.storage import ImageUploadService, get_image_upload_service
from src.utils.errors import AppException, ErrorCode, ExternalServiceError
from src.utils.logger import get_logger


class ChatService:
    def __init__(
        self,
        *,
        qa_client: DifyQAClient,
        elevenlabs_client: ElevenLabsClient,
        storage_service: ImageUploadService,
    ) -> None:
        self.qa_client = qa_client
        self.elevenlabs_client = elevenlabs_client
        self.storage_service = storage_service
        self.logger = get_logger(self.__class__.__name__)

    async def chat(
        self,
        *,
        question: str,
        card_context: str,
        user_id: str,
        user_preference: Optional[str],
        conversation_id: Optional[str],
        image_url: Optional[str],
        need_audio: bool,
    ) -> Dict[str, Optional[str]]:
        qa_result = await self.qa_client.ask(
            question=question,
            card_context=card_context,
            user_id=user_id,
            user_preference=user_preference,
            conversation_id=conversation_id,
            image_url=image_url,
        )

        audio_url = None
        if need_audio and qa_result.answer:
            audio_url = await self._maybe_generate_audio(qa_result)

        return {
            "answer": qa_result.answer,
            "conversation_id": qa_result.conversation_id,
            "audio_url": audio_url,
        }

    async def _maybe_generate_audio(self, qa_result: QAResult) -> Optional[str]:
        try:
            audio_bytes = await self.elevenlabs_client.synthesize_speech(text=qa_result.answer)
            return await self.storage_service.upload_audio(audio_bytes)
        except (ExternalServiceError, AppException) as exc:
            self.logger.warning("问答语音生成失败: %s", exc)
            return None


@lru_cache(maxsize=1)
def get_chat_service() -> ChatService:
    return ChatService(
        qa_client=get_dify_qa_client(),
        elevenlabs_client=get_elevenlabs_client(),
        storage_service=get_image_upload_service(),
    )
