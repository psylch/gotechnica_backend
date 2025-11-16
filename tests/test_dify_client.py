import asyncio
import json

import httpx
import pytest

from src.clients.dify_client import DifyCardGenerationClient, DifyPreprocessingClient, DifyQAClient
from src.utils.errors import ExternalServiceError


def _mock_response(body: dict):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=200, json=body)

    return httpx.MockTransport(handler)


def test_preprocessing_client_parses_json():
    async def run():
        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content)
            assert body["query"] == "bio"
            assert body["inputs"] == {
                "user_preference": "bio",
                "image_input": {
                    "type": "image",
                    "transfer_method": "remote_url",
                    "url": "http://image",
                },
            }
            return httpx.Response(
                status_code=200,
                json={
                    "answer": json.dumps({"image_status": "clear", "central_object": "leaf"}),
                    "conversation_id": "conv-1",
                },
            )

        client = DifyPreprocessingClient(api_key="key", timeout=5, transport=httpx.MockTransport(handler))
        result = await client.analyze(image_url="http://image", user_preference="bio", user_id="u1")

        assert result.image_status == "clear"
        assert result.central_object == "leaf"
        assert result.conversation_id == "conv-1"

    asyncio.run(run())


def test_preprocessing_allows_code_block_json():
    async def run():
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                status_code=200,
                json={"answer": CODE_BLOCK_ANSWER},
            )

        client = DifyPreprocessingClient(api_key="key", timeout=5, transport=httpx.MockTransport(handler))
        result = await client.analyze(image_url="http://image", user_preference="bio", user_id="u1")
        assert result.central_object == "leaf"

    asyncio.run(run())


def test_preprocessing_client_uses_default_query():
    async def run():
        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content)
            assert body["query"] == "DO THIS"
            assert body["inputs"] == {
                "user_preference": "DO THIS",
                "image_input": {
                    "type": "image",
                    "transfer_method": "remote_url",
                    "url": "http://image",
                },
            }
            return httpx.Response(status_code=200, json={"answer": json.dumps({"image_status": "clear"})})

        client = DifyPreprocessingClient(api_key="key", timeout=5, transport=httpx.MockTransport(handler))
        await client.analyze(image_url="http://image", user_preference=None, user_id="u1")

    asyncio.run(run())


def test_card_generation_requires_valid_json():
    async def run():
        transport = _mock_response({"answer": "not json"})
        client = DifyCardGenerationClient(api_key="key", timeout=5, transport=transport)

        with pytest.raises(ExternalServiceError):
            await client.generate_card(
                image_url="http://image",
                central_object="leaf",
                user_preference="bio",
                user_id="u1",
            )

    asyncio.run(run())


def test_card_generation_uses_default_query():
    async def run():
        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content)
            assert body["query"] == "DO THIS"
            assert body["inputs"]["image_input"]["url"] == "http://image"
            return httpx.Response(
                status_code=200,
                json={"answer": json.dumps({"title": "t", "desc": "d"})},
            )

        client = DifyCardGenerationClient(api_key="key", timeout=5, transport=httpx.MockTransport(handler))
        await client.generate_card(
            image_url="http://image",
            central_object="leaf",
            user_preference=None,
            user_id="u1",
        )

    asyncio.run(run())


def test_qa_client_returns_answer():
    async def run():
        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content)
            assert body["inputs"]["user_preference"] == "bio"
            return httpx.Response(status_code=200, json={"answer": "hi", "conversation_id": "c1", "message_id": "m1"})

        client = DifyQAClient(api_key="key", timeout=5, transport=httpx.MockTransport(handler))
        result = await client.ask(
            question="?",
            card_context="Title: x",
            user_id="user",
            user_preference="bio",
        )

        assert result.answer == "hi"
        assert result.conversation_id == "c1"
        assert result.message_id == "m1"

    asyncio.run(run())
CODE_BLOCK_ANSWER = """```json
{
  "image_status": "clear",
  "central_object": "leaf"
}
```"""
