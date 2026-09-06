from collections.abc import AsyncIterator, Iterator
from urllib.parse import parse_qs, urlparse

import boto3
import pytest
from moto import mock_aws

from app.adapters.storage.base import StorageAdapter
from app.adapters.storage.s3 import S3StorageAdapter, make_s3_client

REGION = "us-east-1"
BUCKET = "alma-resumes"


async def _read_all(chunks: AsyncIterator[bytes]) -> bytes:
    return b"".join([chunk async for chunk in chunks])


@pytest.fixture
def bucket(monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", REGION)
    with mock_aws():
        boto3.client("s3", region_name=REGION).create_bucket(Bucket=BUCKET)
        yield BUCKET


async def test_put_then_stream_roundtrip_with_content_type(bucket: str) -> None:
    adapter = S3StorageAdapter(bucket=bucket, region=REGION)
    await adapter.put("resumes/abc.pdf", b"%PDF-1.4 data", "application/pdf")

    assert await _read_all(await adapter.stream("resumes/abc.pdf")) == b"%PDF-1.4 data"
    head = boto3.client("s3", region_name=REGION).head_object(Bucket=bucket, Key="resumes/abc.pdf")
    assert head["ContentType"] == "application/pdf"


async def test_stream_missing_raises_key_error(bucket: str) -> None:
    adapter = S3StorageAdapter(bucket=bucket, region=REGION)
    with pytest.raises(KeyError):
        await adapter.stream("resumes/missing.pdf")


async def test_delete_removes_object_and_tolerates_missing(bucket: str) -> None:
    adapter = S3StorageAdapter(bucket=bucket, region=REGION)
    await adapter.put("k", b"x", "text/plain")
    await adapter.delete("k")
    with pytest.raises(KeyError):
        await adapter.stream("k")
    await adapter.delete("k")  # no raise


async def test_presigned_url_has_expiry_and_signature(bucket: str) -> None:
    adapter = S3StorageAdapter(bucket=bucket, region=REGION)
    url = await adapter.presigned_url("resumes/abc.pdf", expires_in=123)
    assert url is not None

    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    assert parsed.scheme == "https"
    assert bucket in parsed.netloc or parsed.path.startswith(f"/{bucket}/")
    assert parsed.path.endswith("/resumes/abc.pdf")
    assert query["X-Amz-Expires"] == ["123"]
    assert "X-Amz-Signature" in query


async def test_endpoint_override_uses_path_style_urls(bucket: str) -> None:
    endpoint = "https://accountid.r2.cloudflarestorage.com"
    adapter = S3StorageAdapter(bucket=bucket, region="auto", endpoint_url=endpoint)
    url = await adapter.presigned_url("resumes/abc.pdf", expires_in=60)

    assert url is not None
    assert url.startswith(f"{endpoint}/{bucket}/resumes/abc.pdf?")
    assert "X-Amz-Algorithm=AWS4-HMAC-SHA256" in url


def test_make_s3_client_treats_blank_endpoint_as_aws(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    client = make_s3_client(region=REGION, endpoint_url="")
    assert client.meta.endpoint_url.endswith(".amazonaws.com")
    minio = make_s3_client(region=REGION, endpoint_url="http://minio:9000")
    assert minio.meta.endpoint_url == "http://minio:9000"


def test_requires_bucket() -> None:
    with pytest.raises(ValueError):
        S3StorageAdapter(bucket="", region=REGION, client=object())


def test_s3_adapter_satisfies_protocol() -> None:
    assert isinstance(S3StorageAdapter(bucket="b", region=REGION, client=object()), StorageAdapter)
