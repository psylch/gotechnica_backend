from __future__ import annotations

from functools import lru_cache

import httpx

from src.config import get_settings
from src.utils.errors import ExternalServiceError


class ElevenLabsClient:
    BASE_URL = "https://api.elevenlabs.io/v1"

    def __init__(
        self,
        api_key: str,
        voice_id: str,
        timeout: int,
        *,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("ElevenLabs API key is required")
        if not voice_id:
            raise ValueError("ElevenLabs voice id is required")

        self._voice_id = voice_id
        self._timeout = timeout
        self._transport = transport
        self._headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json",
        }

    async def synthesize_speech(
        self,
        *,
        text: str,
        model_id: str = "eleven_flash_v2_5",
        output_format: str = "mp3_22050_32",
    ) -> bytes:
        payload = {
            "model_id": model_id,
            "text": text,
            "output_format": output_format,
        }
        async with httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=self._timeout,
            transport=self._transport,
        ) as client:
            try:
                response = await client.post(
                    f"/text-to-speech/{self._voice_id}",
                    headers=self._headers,
                    json=payload,
                )
                response.raise_for_status()
            except httpx.TimeoutException as exc:
                raise ExternalServiceError("elevenlabs", "ElevenLabs 请求超时") from exc
            except httpx.HTTPStatusError as exc:
                message = exc.response.text or "ElevenLabs 返回错误"
                raise ExternalServiceError(
                    "elevenlabs",
                    message,
                    status_code=exc.response.status_code,
                ) from exc

        return response.content


@lru_cache(maxsize=1)
def get_elevenlabs_client() -> ElevenLabsClient:
    settings = get_settings()
    return ElevenLabsClient(
        api_key=settings.elevenlabs_api_key or "",
        voice_id=settings.elevenlabs_voice_id or "",
        timeout=settings.timeout_elevenlabs_tts,
    )
