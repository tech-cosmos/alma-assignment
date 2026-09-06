from __future__ import annotations

import pytest

from app.adapters.email import (
    ConsoleEmailAdapter,
    SesEmailAdapter,
    SmtpEmailAdapter,
    build_email_adapter,
)
from app.adapters.storage import (
    LocalStorageAdapter,
    S3StorageAdapter,
    build_storage_adapter,
)


def test_build_email_adapter_selects_by_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    assert isinstance(
        build_email_adapter("console", email_from="a@b.c"), ConsoleEmailAdapter
    )
    assert isinstance(
        build_email_adapter(
            "smtp", email_from="a@b.c", smtp_host="mailpit", smtp_port=1025
        ),
        SmtpEmailAdapter,
    )
    assert isinstance(
        build_email_adapter("ses", email_from="a@b.c", aws_region="eu-west-1"),
        SesEmailAdapter,
    )


def test_build_email_adapter_rejects_unknown_provider() -> None:
    with pytest.raises(ValueError, match="EMAIL_PROVIDER"):
        build_email_adapter("pigeon", email_from="a@b.c")


def test_build_storage_adapter_selects_by_provider(
    tmp_path: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    assert isinstance(
        build_storage_adapter("local", local_dir=str(tmp_path)), LocalStorageAdapter
    )
    assert isinstance(
        build_storage_adapter(
            "s3",
            s3_bucket="b",
            s3_endpoint_url="http://minio:9000",
            aws_region="us-east-1",
        ),
        S3StorageAdapter,
    )


def test_build_storage_adapter_rejects_unknown_provider() -> None:
    with pytest.raises(ValueError, match="STORAGE_PROVIDER"):
        build_storage_adapter("floppy")


def test_build_storage_adapter_s3_requires_bucket() -> None:
    with pytest.raises(ValueError, match="S3_BUCKET"):
        build_storage_adapter("s3", s3_bucket="")
