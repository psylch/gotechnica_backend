from __future__ import annotations

from typing import Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from src.config import AppSettings


class R2ClientError(RuntimeError):
    pass


class R2Client:
    def __init__(
        self,
        settings: AppSettings,
        *,
        boto_client: Optional[object] = None,
    ) -> None:
        if not all(
            [
                settings.r2_account_id,
                settings.r2_access_key_id,
                settings.r2_secret_access_key,
                settings.r2_bucket_name,
                settings.r2_public_url,
            ]
        ):
            raise R2ClientError("R2 configuration is incomplete")

        endpoint = settings.r2_endpoint_url
        if endpoint is None:
            raise R2ClientError("R2 endpoint could not be constructed")

        self._bucket = settings.r2_bucket_name
        self._public_url = settings.r2_public_url.rstrip("/")
        self._client = boto_client or boto3.client(
            "s3",
            region_name="auto",
            endpoint_url=endpoint,
            aws_access_key_id=settings.r2_access_key_id,
            aws_secret_access_key=settings.r2_secret_access_key,
        )

    def upload_file(self, *, key: str, data: bytes, content_type: str) -> str:
        try:
            self._client.put_object(Bucket=self._bucket, Key=key, Body=data, ContentType=content_type)
        except (ClientError, BotoCoreError) as exc:
            raise R2ClientError(str(exc)) from exc

        return f"{self._public_url}/{key}"
