import asyncio
import base64
from unittest.mock import patch

import pytest

from src.clients.gemini_client import GeminiClient
from src.utils.errors import ExternalServiceError


class DummyMessage:
    def __init__(self, images=None):
        self.images = images or []


class DummyChoice:
    def __init__(self, message):
        self.message = message


class DummyCompletion:
    def __init__(self, message):
        self.choices = [DummyChoice(message)]


class DummyCompletions:
    def __init__(self, response):
        self._response = response
        self.last_kwargs = None

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        return self._response


class DummyChat:
    def __init__(self, response):
        self.completions = DummyCompletions(response)


class DummyOpenAI:
    def __init__(self, response):
        self.chat = DummyChat(response)


def test_gemini_client_returns_bytes_from_data_url():
    async def run():
        encoded = base64.b64encode(b"png-data").decode("utf-8")
        response = DummyCompletion(
            DummyMessage(images=[{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{encoded}"}}])
        )
        dummy_client = DummyOpenAI(response)

        client = GeminiClient(
            api_key="key",
            base_url="https://openrouter.ai/api/v1",
            timeout=5,
            site_url="https://example.com",
            site_name="Example",
            openai_client=dummy_client,
        )

        result = await client.highlight_object("http://image", "prompt")

        assert result == b"png-data"
        messages = dummy_client.chat.completions.last_kwargs["messages"]
        assert messages[0]["content"][1]["image_url"]["url"] == "http://image"

    asyncio.run(run())


def test_gemini_client_downloads_remote_image_when_not_data_url():
    async def run():
        response = DummyCompletion(
            DummyMessage(images=[{"type": "image_url", "image_url": {"url": "https://file.example.com/img.png"}}])
        )
        dummy_client = DummyOpenAI(response)

        client = GeminiClient(
            api_key="key",
            base_url="https://openrouter.ai/api/v1",
            timeout=5,
            openai_client=dummy_client,
        )

        with patch("httpx.get") as mock_get:
            class Resp:
                content = b"bytes"

                def raise_for_status(self):
                    return None

            mock_get.return_value = Resp()
            data = await client.highlight_object("http://image", "prompt")
            assert data == b"bytes"

    asyncio.run(run())


def test_gemini_client_errors_when_no_image():
    async def run():
        response = DummyCompletion(DummyMessage(images=[]))
        client = GeminiClient(
            api_key="key",
            base_url="https://openrouter.ai/api/v1",
            timeout=5,
            openai_client=DummyOpenAI(response),
        )

        with pytest.raises(ExternalServiceError):
            await client.highlight_object("http://image", "prompt")

    asyncio.run(run())
