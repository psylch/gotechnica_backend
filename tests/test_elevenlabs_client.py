import asyncio

import httpx
import pytest

from src.clients.elevenlabs_client import ElevenLabsClient
from src.utils.errors import ExternalServiceError


def test_elevenlabs_client_returns_audio_bytes():
    async def run():
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers["xi-api-key"] == "key"
            return httpx.Response(200, content=b"audio-bytes")

        client = ElevenLabsClient(
            api_key="key",
            voice_id="aria",
            timeout=5,
            transport=httpx.MockTransport(handler),
        )

        content = await client.synthesize_speech(text="hello world")
        assert content == b"audio-bytes"

    asyncio.run(run())


def test_elevenlabs_client_handles_http_error():
    async def run():
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, json={"error": "invalid"})

        client = ElevenLabsClient(
            api_key="key",
            voice_id="aria",
            timeout=5,
            transport=httpx.MockTransport(handler),
        )

        with pytest.raises(ExternalServiceError):
            await client.synthesize_speech(text="hello world")

    asyncio.run(run())
