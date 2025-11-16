import asyncio
from io import BytesIO

import pytest
from fastapi import UploadFile
from starlette.datastructures import Headers

from src.clients.r2_client import R2ClientError
from src.services.storage import ImageUploadService
from src.utils.errors import AppException, ErrorCode


class DummyR2Client:
    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail
        self.last_key = None
        self.last_content_type = None
        self.data = None

    def upload_file(self, *, key: str, data: bytes, content_type: str) -> str:
        if self.should_fail:
            raise R2ClientError("boom")
        self.last_key = key
        self.last_content_type = content_type
        self.data = data
        return f"https://files.example.com/{key}"


def make_upload_file(filename: str, content: bytes, content_type: str) -> UploadFile:
    file = BytesIO(content)
    headers = Headers({"content-type": content_type})
    return UploadFile(filename=filename, file=file, headers=headers)


def test_upload_original_image_success():
    client = DummyR2Client()
    service = ImageUploadService(client)  # type: ignore[arg-type]

    upload = make_upload_file("sample.jpg", b"data", "image/jpeg")
    url = asyncio.run(service.upload_original_image(upload))

    assert url.startswith("https://files.example.com/original_image/")
    assert client.last_key.endswith(".jpg")
    assert client.last_content_type == "image/jpeg"
    assert client.data == b"data"


def test_upload_rejects_invalid_extension():
    client = DummyR2Client()
    service = ImageUploadService(client)  # type: ignore[arg-type]

    upload = make_upload_file("sample.txt", b"data", "text/plain")

    with pytest.raises(AppException) as exc:
        asyncio.run(service.upload_original_image(upload))

    assert exc.value.error_code == ErrorCode.VALIDATION_ERROR


def test_upload_handles_r2_failure():
    client = DummyR2Client(should_fail=True)
    service = ImageUploadService(client)  # type: ignore[arg-type]

    upload = make_upload_file("sample.jpg", b"data", "image/jpeg")

    with pytest.raises(AppException) as exc:
        asyncio.run(service.upload_original_image(upload))

    assert exc.value.error_code == ErrorCode.STORAGE_ERROR
