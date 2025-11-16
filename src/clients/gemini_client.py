from __future__ import annotations

from base64 import b64decode
from functools import lru_cache
from typing import Optional

import anyio
import httpx
from openai import OpenAI

from src.config import get_settings
from src.utils.errors import ExternalServiceError


class GeminiClient:
    MODEL_ID = "google/gemini-2.5-flash-image"

    def __init__(
        self,
        api_key: str,
        base_url: str,
        timeout: int,
        *,
        site_url: Optional[str] = None,
        site_name: Optional[str] = None,
        openai_client: OpenAI | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("OpenRouter API key is required")

        self._timeout = timeout
        self._headers = {}
        if site_url:
            self._headers["HTTP-Referer"] = site_url
        if site_name:
            self._headers["X-Title"] = site_name
        self._client = openai_client or OpenAI(base_url=base_url, api_key=api_key, timeout=timeout)

    async def highlight_object(self, image_url: str, prompt: str) -> bytes:
        return await anyio.to_thread.run_sync(self._generate_image_bytes, image_url, prompt)

    def _generate_image_bytes(self, image_url: str, prompt: str) -> bytes:
        try:
            completion = self._client.chat.completions.create(
                extra_headers=self._headers,
                model=self.MODEL_ID,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": image_url}},
                        ],
                    }
                ],
            )
        except Exception as exc:  # pragma: no cover - third-party raises many subclasses
            raise ExternalServiceError("gemini", f"OpenRouter 调用失败: {exc}") from exc

        message = self._extract_message(completion)
        return self._extract_image_bytes(message)

    @staticmethod
    def _extract_message(completion) -> object:
        choices = getattr(completion, "choices", None)
        if not choices:
            raise ExternalServiceError("gemini", "OpenRouter 未返回任何响应")
        message = getattr(choices[0], "message", None)
        if message is None:
            raise ExternalServiceError("gemini", "OpenRouter 响应缺少 message 字段")
        return message

    def _extract_image_bytes(self, message) -> bytes:
        images = getattr(message, "images", None)
        if not images:
            raise ExternalServiceError("gemini", "OpenRouter 未返回图像结果")

        data_url = images[0].get("image_url", {}).get("url")
        if not data_url:
            raise ExternalServiceError("gemini", "OpenRouter 图像数据缺失")

        if data_url.startswith("data:"):
            return self._decode_data_url(data_url)
        if data_url.startswith("http"):
            return self._download_image(data_url)
        raise ExternalServiceError("gemini", "不支持的图片数据格式")

    @staticmethod
    def _decode_data_url(data_url: str) -> bytes:
        try:
            _, encoded = data_url.split(",", 1)
        except ValueError as exc:
            raise ExternalServiceError("gemini", "无效的 data URL") from exc
        return b64decode(encoded)

    def _download_image(self, url: str) -> bytes:
        try:
            response = httpx.get(url, timeout=self._timeout)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ExternalServiceError("gemini", f"下载生成的图片失败: {exc}") from exc
        return response.content


@lru_cache(maxsize=1)
def get_gemini_client() -> GeminiClient:
    settings = get_settings()
    return GeminiClient(
        api_key=settings.openrouter_api_key or "",
        base_url=settings.openrouter_base_url,
        timeout=settings.timeout_gemini_highlight,
        site_url=settings.openrouter_site_url,
        site_name=settings.openrouter_site_name,
    )
