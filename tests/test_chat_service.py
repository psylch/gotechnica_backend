import asyncio

import pytest

from src.clients.dify_client import QAResult
from src.services.chat import ChatService
from src.utils.errors import ExternalServiceError


class DummyQAClient:
    def __init__(self, result: QAResult):
        self.result = result

    async def ask(self, **kwargs):
        self.kwargs = kwargs
        return self.result


class DummyElevenLabsClient:
    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail

    async def synthesize_speech(self, text: str):
        if self.should_fail:
            raise ExternalServiceError("tts", "fail")
        self.last_text = text
        return b"audio"


class DummyStorageService:
    async def upload_audio(self, data: bytes, extension: str = "mp3"):
        self.data = data
        return "https://files/audio.mp3"


def build_service(answer: str = "hello", audio_fail: bool = False):
    return ChatService(
        qa_client=DummyQAClient(QAResult(answer=answer, conversation_id="conv")),
        elevenlabs_client=DummyElevenLabsClient(should_fail=audio_fail),
        storage_service=DummyStorageService(),
    )


def test_chat_service_with_audio():
    service = build_service()

    async def run():
        result = await service.chat(
            question="?",
            card_context="ctx",
            user_id="user",
            user_preference="bio",
            conversation_id="conv",
            image_url="http://image",
            need_audio=True,
        )
        assert result["answer"] == "hello"
        assert result["conversation_id"] == "conv"
        assert result["audio_url"] == "https://files/audio.mp3"

    asyncio.run(run())


def test_chat_service_audio_failure_downgrades():
    service = build_service(audio_fail=True)

    async def run():
        result = await service.chat(
            question="?",
            card_context="ctx",
            user_id="user",
            user_preference=None,
            conversation_id=None,
            image_url=None,
            need_audio=True,
        )
        assert result["audio_url"] is None

    asyncio.run(run())


def test_chat_service_without_audio():
    service = build_service()

    async def run():
        result = await service.chat(
            question="?",
            card_context="ctx",
            user_id="user",
            user_preference=None,
            conversation_id=None,
            image_url=None,
            need_audio=False,
        )
        assert result["audio_url"] is None

    asyncio.run(run())
