# backend/app/services/storage.py
"""S3-compatible object storage service (MinIO locally, R2/S3 in prod)."""

import json
import uuid

import aioboto3
from botocore.exceptions import ClientError

from app.core.config import get_settings

_session: aioboto3.Session | None = None


def _get_session() -> aioboto3.Session:
    global _session
    if _session is None:
        _session = aioboto3.Session()
    return _session


class StorageService:
    def __init__(self) -> None:
        settings = get_settings()
        self._settings = settings
        self._session = _get_session()
        self._base_url = settings.MEDIA_BASE_URL.rstrip("/")

    def _client(self):
        return self._session.client(
            "s3",
            endpoint_url=self._settings.S3_ENDPOINT_URL,
            aws_access_key_id=self._settings.S3_ACCESS_KEY,
            aws_secret_access_key=self._settings.S3_SECRET_KEY,
            region_name=self._settings.S3_REGION,
        )

    async def upload_image(self, data: bytes, content_type: str, ext: str) -> str:
        """Upload image bytes to a random key, return public URL."""
        return await self.upload_at_key(
            data, f"items/{uuid.uuid4().hex}.{ext}", content_type
        )

    async def upload_audio(self, data: bytes, content_type: str, ext: str) -> str:
        """Upload audio bytes to a random key, return public URL."""
        return await self.upload_at_key(
            data, f"audio/{uuid.uuid4().hex}.{ext}", content_type
        )

    async def get_url_if_exists(self, key: str) -> str | None:
        """Return public URL if key exists in bucket, else None. Used for cache checks."""
        async with self._client() as s3:
            try:
                await s3.head_object(Bucket=self._settings.S3_BUCKET, Key=key)
                return f"{self._base_url}/{key}"
            except ClientError as e:
                code = e.response["Error"]["Code"]
                if code in ("404", "NoSuchKey"):
                    return None
                raise

    async def upload_at_key(
        self, data: bytes, key: str, content_type: str = "application/octet-stream"
    ) -> str:
        """Upload bytes to a specific deterministic key, return public URL."""
        async with self._client() as s3:
            await s3.put_object(
                Bucket=self._settings.S3_BUCKET,
                Key=key,
                Body=data,
                ContentType=content_type,
            )
        return f"{self._base_url}/{key}"

    async def delete(self, url: str) -> None:
        """Delete object by public URL. No-op if URL doesn't belong to this bucket."""
        prefix = self._base_url + "/"
        if not url.startswith(prefix):
            return
        key = url[len(prefix):]
        async with self._client() as s3:
            await s3.delete_object(Bucket=self._settings.S3_BUCKET, Key=key)

    async def ensure_bucket(self) -> None:
        """Create bucket if missing and apply public-read policy."""
        async with self._client() as s3:
            try:
                await s3.head_bucket(Bucket=self._settings.S3_BUCKET)
            except ClientError:
                await s3.create_bucket(Bucket=self._settings.S3_BUCKET)

            policy = json.dumps({
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": {"AWS": ["*"]},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{self._settings.S3_BUCKET}/*"],
                }],
            })
            await s3.put_bucket_policy(
                Bucket=self._settings.S3_BUCKET,
                Policy=policy,
            )


__all__ = ["StorageService"]
