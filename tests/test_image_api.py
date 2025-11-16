from fastapi.testclient import TestClient

from src.api import images
from src.main import app


class StubUploadService:
    async def upload_original_image(self, upload):
        await upload.read()
        return "https://files.example.com/original_image/test.jpg"


def test_image_upload_endpoint_returns_url():
    app.dependency_overrides[images.get_upload_service] = lambda: StubUploadService()
    client = TestClient(app)

    try:
        response = client.post(
            "/api/v1/images/upload",
            files={"file": ("sample.jpg", b"hello", "image/jpeg")},
        )

        assert response.status_code == 201
        assert response.json() == {"success": True, "url": "https://files.example.com/original_image/test.jpg"}
    finally:
        app.dependency_overrides.pop(images.get_upload_service, None)
