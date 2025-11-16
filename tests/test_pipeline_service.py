import asyncio

import pytest

from src.clients.dify_client import CardGenerationResult, PreprocessResult
from src.services.pipeline import PipelineService
from src.utils.errors import AppException, ErrorCode, ExternalServiceError


class DummyPreprocessClient:
    def __init__(self, result: PreprocessResult):
        self.result = result

    async def analyze(self, **kwargs):
        self.kwargs = kwargs
        return self.result


class DummyCardClient:
    def __init__(self, result: CardGenerationResult):
        self.result = result

    async def generate_card(self, **kwargs):
        self.kwargs = kwargs
        return self.result


class DummyGeminiClient:
    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail

    async def highlight_object(self, **kwargs):
        if self.should_fail:
            raise ExternalServiceError("gemini", "fail")
        self.kwargs = kwargs
        return b"img-bytes"


class DummyElevenLabsClient:
    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail

    async def synthesize_speech(self, text: str):
        if self.should_fail:
            raise ExternalServiceError("tts", "fail")
        self.last_text = text
        return b"audio"


class DummyStorageService:
    def __init__(self):
        self.highlight_data = None
        self.audio_data = None

    async def upload_highlight_image(self, data: bytes, extension: str = "png"):
        self.highlight_data = data
        return "https://files/highlight.png"

    async def upload_audio(self, data: bytes, extension: str = "mp3"):
        self.audio_data = data
        return "https://files/audio.mp3"


def build_service(
    *,
    preprocess: PreprocessResult,
    card: CardGenerationResult,
    gemini_fail: bool = False,
    audio_fail: bool = False,
):
    return PipelineService(
        preprocess_client=DummyPreprocessClient(preprocess),
        card_client=DummyCardClient(card),
        gemini_client=DummyGeminiClient(should_fail=gemini_fail),
        elevenlabs_client=DummyElevenLabsClient(should_fail=audio_fail),
        storage_service=DummyStorageService(),
        logger=type("Logger", (), {"info": lambda *a, **k: None, "warning": lambda *a, **k: None})(),
    )


def test_pipeline_success_path():
    preprocess = PreprocessResult(image_status="clear", central_object="camera")
    card = CardGenerationResult(title="Title", desc="Desc")
    service = build_service(preprocess=preprocess, card=card)

    async def run():
        result = await service.generate_card({"image_url": "http://img", "user_preference": "biology"})
        assert result["title"] == "Title"
        assert result["central_object"] == "camera"
        assert result["highlighted_image_url"] == "https://files/highlight.png"
        assert result["audio_url"] == "https://files/audio.mp3"

    asyncio.run(run())


def test_pipeline_handles_unclear_image():
    preprocess = PreprocessResult(image_status="unclear")
    card = CardGenerationResult(title="Title", desc="Desc")
    service = build_service(preprocess=preprocess, card=card)

    async def run():
        with pytest.raises(AppException) as exc:
            await service.generate_card({"image_url": "http://img"})
        assert exc.value.error_code == ErrorCode.VALIDATION_ERROR

    asyncio.run(run())


def test_pipeline_downgrades_when_highlight_fails():
    preprocess = PreprocessResult(image_status="clear", central_object="camera")
    card = CardGenerationResult(title="Title", desc="Desc")
    service = build_service(preprocess=preprocess, card=card, gemini_fail=True, audio_fail=True)

    async def run():
        result = await service.generate_card({"image_url": "http://img"})
        assert result["highlighted_image_url"] is None
        assert result["audio_url"] is None

    asyncio.run(run())
