from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, Optional

import httpx
import re

from src.config import get_settings
from src.utils.errors import ExternalServiceError

DEFAULT_QUERY = "DO THIS"


def _build_image_payload(image_url: str) -> Dict[str, str]:
    return {
        "type": "image",
        "transfer_method": "remote_url",
        "url": image_url,
    }


class DifyClient:
    BASE_URL = "https://api.dify.ai/v1"

    def __init__(self, api_key: str, timeout: int, *, transport: httpx.BaseTransport | None = None) -> None:
        if not api_key:
            raise ValueError("Dify API key is required")

        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        self._timeout = timeout
        self._transport = transport

    async def send_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if "inputs" not in payload:
            payload = {**payload, "inputs": {}}
        request_body = {
            "response_mode": "blocking",
            "conversation_id": payload.get("conversation_id") or "",
            "user": payload.get("user") or "snapopedia",
            **payload,
        }

        async with httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=self._timeout,
            transport=self._transport,
        ) as client:
            try:
                response = await client.post("/chat-messages", headers=self._headers, json=request_body)
                response.raise_for_status()
            except httpx.TimeoutException as exc:
                raise ExternalServiceError("dify", "Dify request timed out") from exc
            except httpx.HTTPStatusError as exc:
                error_message = exc.response.text or "Dify returned an error"
                raise ExternalServiceError(
                    "dify", error_message, status_code=exc.response.status_code
                ) from exc

        try:
            return response.json()
        except ValueError as exc:
            raise ExternalServiceError("dify", "Invalid JSON response from Dify") from exc


@dataclass
class PreprocessResult:
    image_status: str
    central_object: Optional[str] = None
    conversation_id: Optional[str] = None


@dataclass
class CardGenerationResult:
    title: str
    desc: str
    conversation_id: Optional[str] = None


@dataclass
class QAResult:
    answer: str
    conversation_id: Optional[str] = None
    message_id: Optional[str] = None


class DifyPreprocessingClient:
    def __init__(self, api_key: str, timeout: int, *, transport: httpx.BaseTransport | None = None) -> None:
        self._client = DifyClient(api_key=api_key, timeout=timeout, transport=transport)

    async def analyze(
        self,
        *,
        image_url: str,
        user_preference: Optional[str],
        user_id: str,
    ) -> PreprocessResult:
        normalized_preference = user_preference or DEFAULT_QUERY
        payload = {
            "query": normalized_preference,
            "inputs": {
                "user_preference": normalized_preference,
                "image_input": _build_image_payload(image_url),
            },
            "files": [_build_image_payload(image_url)],
            "user": user_id,
        }
        response = await self._client.send_message(payload)
        parsed = self._parse_answer(response.get("answer", ""))
        return PreprocessResult(
            image_status=parsed["image_status"],
            central_object=parsed.get("central_object"),
            conversation_id=response.get("conversation_id"),
        )

    @staticmethod
    def _parse_answer(answer: str) -> Dict[str, Any]:
        try:
            parsed = json.loads(_extract_json_payload(answer))
        except json.JSONDecodeError as exc:
            raise ExternalServiceError("dify", "预处理 workflow 返回的 answer 不是有效 JSON") from exc

        if "image_status" not in parsed:
            raise ExternalServiceError("dify", "缺少 image_status 字段")
        return parsed


class DifyCardGenerationClient:
    def __init__(self, api_key: str, timeout: int, *, transport: httpx.BaseTransport | None = None) -> None:
        self._client = DifyClient(api_key=api_key, timeout=timeout, transport=transport)

    async def generate_card(
        self,
        *,
        image_url: str,
        central_object: str,
        user_preference: Optional[str],
        user_id: str,
    ) -> CardGenerationResult:
        normalized_preference = user_preference or DEFAULT_QUERY
        payload = {
            "query": normalized_preference,
            "inputs": {
                "item_name": central_object,
                "user_preference": normalized_preference,
                "image_input": _build_image_payload(image_url),
            },
            "files": [_build_image_payload(image_url)],
            "user": user_id,
        }
        response = await self._client.send_message(payload)
        parsed = self._parse_answer(response.get("answer", ""))
        return CardGenerationResult(
            title=parsed["title"],
            desc=parsed["desc"],
            conversation_id=response.get("conversation_id"),
        )

    @staticmethod
    def _parse_answer(answer: str) -> Dict[str, Any]:
        try:
            parsed = json.loads(_extract_json_payload(answer))
        except json.JSONDecodeError as exc:
            raise ExternalServiceError("dify", "卡片生成 workflow 返回的 answer 不是有效 JSON") from exc

        if "title" not in parsed or "desc" not in parsed:
            raise ExternalServiceError("dify", "卡片生成 workflow 缺少 title/desc 字段")
        return parsed


class DifyQAClient:
    def __init__(self, api_key: str, timeout: int, *, transport: httpx.BaseTransport | None = None) -> None:
        self._client = DifyClient(api_key=api_key, timeout=timeout, transport=transport)

    async def ask(
        self,
        *,
        question: str,
        card_context: str,
        user_id: str,
        conversation_id: Optional[str] = None,
        image_url: Optional[str] = None,
        user_preference: Optional[str] = None,
    ) -> QAResult:
        preference = user_preference or DEFAULT_QUERY
        inputs: Dict[str, Any] = {"card_context": card_context, "user_preference": preference}
        files = None
        if image_url:
            payload_image = _build_image_payload(image_url)
            inputs["image_input"] = payload_image
            files = [payload_image]

        payload: Dict[str, Any] = {
            "query": question,
            "inputs": inputs,
            "user": user_id,
            "conversation_id": conversation_id or "",
        }
        if files:
            payload["files"] = files

        response = await self._client.send_message(payload)
        return QAResult(
            answer=response.get("answer", ""),
            conversation_id=response.get("conversation_id"),
            message_id=response.get("message_id"),
        )


@lru_cache(maxsize=1)
def get_dify_preprocessing_client() -> DifyPreprocessingClient:
    settings = get_settings()
    return DifyPreprocessingClient(
        api_key=settings.dify_api_key_preprocessing or "",
        timeout=settings.timeout_dify_preprocessing,
    )


@lru_cache(maxsize=1)
def get_dify_card_generation_client() -> DifyCardGenerationClient:
    settings = get_settings()
    return DifyCardGenerationClient(
        api_key=settings.dify_api_key_card_gen or "",
        timeout=settings.timeout_dify_card_gen,
    )


@lru_cache(maxsize=1)
def get_dify_qa_client() -> DifyQAClient:
    settings = get_settings()
    return DifyQAClient(
        api_key=settings.dify_api_key_qa or "",
        timeout=settings.timeout_dify_qa,
    )
CODE_BLOCK_PATTERN = re.compile(r"^```(?:json)?\s*(?P<body>.*?)\s*```$", re.DOTALL | re.IGNORECASE)


def _extract_json_payload(answer: str) -> str:
    text = answer.strip()
    match = CODE_BLOCK_PATTERN.match(text)
    if match:
        return match.group("body").strip()
    return text
