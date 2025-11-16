from __future__ import annotations

import time
from functools import lru_cache
from http import HTTPStatus
from typing import Dict, Optional
from uuid import uuid4

from fastapi import UploadFile

from src.clients.r2_client import R2Client, R2ClientError
from src.config import get_settings
from src.utils.errors import AppException, ErrorCode
from src.utils.logger import get_logger

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
CONTENT_TYPE_MAPPING: Dict[str, str] = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
}


class ImageUploadService:
    def __init__(self, r2_client: R2Client):
        self._r2_client = r2_client
        self._logger = get_logger(self.__class__.__name__)

    async def upload_original_image(self, upload: UploadFile) -> str:
        extension = self._resolve_extension(upload)
        if extension not in ALLOWED_EXTENSIONS:
            raise AppException(
                error_code=ErrorCode.VALIDATION_ERROR,
                message="仅支持 jpg/png/webp 图片",
                status_code=HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
            )

        content = await upload.read()
        if not content:
            raise AppException(error_code=ErrorCode.VALIDATION_ERROR, message="上传文件为空")

        key = self._build_storage_key("original_image", extension)
        return self._upload_bytes(key=key, data=content, content_type=CONTENT_TYPE_MAPPING[extension])

    async def upload_highlight_image(self, data: bytes, extension: str = "png") -> str:
        key = self._build_storage_key("highlighted_image", extension)
        return self._upload_bytes(key=key, data=data, content_type=f"image/{extension}")

    async def upload_audio(self, data: bytes, extension: str = "mp3") -> str:
        key = self._build_storage_key("card_audio", extension)
        return self._upload_bytes(key=key, data=data, content_type="audio/mpeg")

    def _resolve_extension(self, upload: UploadFile) -> str:
        if upload.filename:
            suffix = upload.filename.lower().rsplit(".", 1)
            if len(suffix) == 2:
                return self._normalize_extension(suffix[1])

        guessed = self._guess_extension_from_content_type(upload.content_type)
        return guessed or ""

    @staticmethod
    def _guess_extension_from_content_type(content_type: Optional[str]) -> Optional[str]:
        if content_type:
            mapping = {v: k for k, v in CONTENT_TYPE_MAPPING.items()}
            extension = mapping.get(content_type)
            if extension:
                return ImageUploadService._normalize_extension(extension)
        return None

    @staticmethod
    def _normalize_extension(extension: str) -> str:
        if extension == "jpeg":
            return "jpg"
        return extension

    @staticmethod
    def _build_storage_key(prefix: str, extension: str) -> str:
        timestamp = int(time.time())
        random_id = uuid4().hex[:8]
        return f"{prefix}/{timestamp}_{random_id}.{extension}"

    def _upload_bytes(self, *, key: str, data: bytes, content_type: str) -> str:
        try:
            url = self._r2_client.upload_file(key=key, data=data, content_type=content_type)
        except R2ClientError as exc:
            self._logger.error("R2 上传失败: %s", exc)
            raise AppException(error_code=ErrorCode.STORAGE_ERROR, message="文件上传失败", status_code=502) from exc

        self._logger.info("R2 已上传 key=%s", key)
        return url


@lru_cache(maxsize=1)
def get_r2_client() -> R2Client:
    settings = get_settings()
    return R2Client(settings)


@lru_cache(maxsize=1)
def get_image_upload_service() -> ImageUploadService:
    return ImageUploadService(get_r2_client())
