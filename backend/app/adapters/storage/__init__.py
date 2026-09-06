"""Storage adapters. Select one with ``build_storage_adapter``."""

from __future__ import annotations

from .base import StorageAdapter
from .local import LocalStorageAdapter
from .s3 import S3StorageAdapter

STORAGE_PROVIDERS = ("local", "s3")


def build_storage_adapter(
    provider: str,
    *,
    local_dir: str = "/data/resumes",
    local_url_prefix: str = "/api/v1/storage",
    s3_bucket: str = "",
    s3_endpoint_url: str | None = None,
    aws_region: str = "us-east-1",
) -> StorageAdapter:
    """Return the adapter named by ``STORAGE_PROVIDER`` (``local`` | ``s3``)."""
    match provider:
        case "local":
            return LocalStorageAdapter(base_dir=local_dir, url_prefix=local_url_prefix)
        case "s3":
            return S3StorageAdapter(
                bucket=s3_bucket, region=aws_region, endpoint_url=s3_endpoint_url
            )
        case _:
            raise ValueError(
                f"Unknown STORAGE_PROVIDER {provider!r}; expected {STORAGE_PROVIDERS}"
            )


__all__ = [
    "STORAGE_PROVIDERS",
    "LocalStorageAdapter",
    "S3StorageAdapter",
    "StorageAdapter",
    "build_storage_adapter",
]
