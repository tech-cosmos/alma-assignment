"""S3-compatible storage adapter (AWS S3, Cloudflare R2, MinIO).

One boto3 code path for all three: set ``endpoint_url`` for R2/MinIO and leave
it empty for AWS. SigV4 and path-style addressing are forced when an endpoint
override is present, which is what R2 and MinIO expect. boto3 is synchronous,
so network calls run in a worker thread.
"""

from __future__ import annotations

import asyncio
from typing import Any

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

_NOT_FOUND_CODES = {"NoSuchKey", "404", "NotFound"}


def make_s3_client(*, region: str, endpoint_url: str | None) -> Any:
    endpoint = endpoint_url or None
    config = Config(
        signature_version="s3v4",
        s3={"addressing_style": "path" if endpoint else "auto"},
    )
    return boto3.client("s3", region_name=region, endpoint_url=endpoint, config=config)


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

    async def get_url(self, key: str, expires_in: int = 900) -> str:
        url: str = await asyncio.to_thread(
            self._client.generate_presigned_url,
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires_in,
        )
        return url

    async def open(self, key: str) -> bytes:
        try:
            response = await asyncio.to_thread(
                self._client.get_object, Bucket=self._bucket, Key=key
            )
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in _NOT_FOUND_CODES:
                raise FileNotFoundError(key) from exc
            raise
        body: bytes = await asyncio.to_thread(response["Body"].read)
        return body
