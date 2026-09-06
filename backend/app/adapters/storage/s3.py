"""S3-compatible storage adapter (AWS S3, Cloudflare R2, MinIO).

One boto3 code path for all three: set ``S3_ENDPOINT_URL`` for R2/MinIO and leave
it empty for AWS. SigV4 and path-style addressing are forced when an endpoint
override is present, which is what R2 and MinIO expect. boto3 is synchronous,
so network calls run in a worker thread.
"""

import asyncio
from collections.abc import AsyncIterator
from typing import Any

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.adapters.storage.base import StorageAdapter
from app.core.config import Settings

_NOT_FOUND_CODES = {"NoSuchKey", "404", "NotFound"}
CHUNK_SIZE = 64 * 1024


def make_s3_client(*, region: str, endpoint_url: str | None) -> Any:
    endpoint = endpoint_url or None
    config = Config(
        signature_version="s3v4",
        s3={"addressing_style": "path" if endpoint else "auto"},
    )
    return boto3.client("s3", region_name=region, endpoint_url=endpoint, config=config)


def _is_not_found(exc: ClientError) -> bool:
    code = exc.response.get("Error", {}).get("Code")
    return code in _NOT_FOUND_CODES


class S3StorageAdapter:
    def __init__(
        self,
        *,
        bucket: str,
        region: str,
        endpoint_url: str | None = None,
        client: Any | None = None,
    ) -> None:
        if not bucket:
            raise ValueError("S3_BUCKET is required when STORAGE_PROVIDER=s3")
        self._bucket = bucket
        self._client = (
            client
            if client is not None
            else make_s3_client(region=region, endpoint_url=endpoint_url)
        )

    async def put(self, key: str, data: bytes, content_type: str) -> None:
        await asyncio.to_thread(
            self._client.put_object,
            Bucket=self._bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )

    async def delete(self, key: str) -> None:
        # S3 DeleteObject is idempotent: a missing key still returns 204.
        await asyncio.to_thread(self._client.delete_object, Bucket=self._bucket, Key=key)

    async def stream(self, key: str) -> AsyncIterator[bytes]:
        try:
            response = await asyncio.to_thread(
                self._client.get_object, Bucket=self._bucket, Key=key
            )
        except ClientError as exc:
            if _is_not_found(exc):
                raise KeyError(key) from exc
            raise
        body = response["Body"]

        async def chunks() -> AsyncIterator[bytes]:
            try:
                while chunk := await asyncio.to_thread(body.read, CHUNK_SIZE):
                    yield chunk
            finally:
                body.close()

        return chunks()

    async def presigned_url(self, key: str, *, expires_in: int) -> str | None:
        url: str = await asyncio.to_thread(
            self._client.generate_presigned_url,
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires_in,
        )
        return url


def create_adapter(settings: Settings) -> StorageAdapter:
    return S3StorageAdapter(
        bucket=settings.s3_bucket,
        region=settings.aws_region,
        endpoint_url=settings.s3_endpoint_url or None,
    )
