"""The real selection path: ``app.api.deps`` imports ``app.adapters.<kind>.<provider>``
and calls ``create_adapter(settings)``."""

from pathlib import Path

import pytest

from app.adapters.email.base import EmailAdapter
from app.adapters.email.console import ConsoleEmailAdapter
from app.adapters.email.ses import SesEmailAdapter
from app.adapters.email.smtp import SmtpEmailAdapter
from app.adapters.storage.base import StorageAdapter
from app.adapters.storage.local import LocalStorageAdapter
from app.adapters.storage.s3 import S3StorageAdapter
from app.api.deps import _load_adapter
from app.core.config import Settings


@pytest.fixture(autouse=True)
def aws_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")


@pytest.mark.parametrize(
    ("provider", "cls"),
    [("console", ConsoleEmailAdapter), ("smtp", SmtpEmailAdapter), ("ses", SesEmailAdapter)],
)
def test_every_email_provider_is_loadable(provider: str, cls: type) -> None:
    settings = Settings(email_provider=provider)  # type: ignore[arg-type]
    adapter = _load_adapter("email", provider, settings)
    assert isinstance(adapter, cls)
    assert isinstance(adapter, EmailAdapter)


def test_every_storage_provider_is_loadable(tmp_path: Path) -> None:
    local = _load_adapter("storage", "local", Settings(storage_local_dir=str(tmp_path)))
    assert isinstance(local, LocalStorageAdapter)
    assert isinstance(local, StorageAdapter)

    s3 = _load_adapter(
        "storage", "s3", Settings(s3_bucket="b", s3_endpoint_url="http://minio:9000")
    )
    assert isinstance(s3, S3StorageAdapter)
    assert isinstance(s3, StorageAdapter)


def test_unknown_provider_fails_loudly() -> None:
    with pytest.raises(RuntimeError, match="No email adapter named 'pigeon'"):
        _load_adapter("email", "pigeon", Settings())


def test_s3_requires_bucket() -> None:
    with pytest.raises(ValueError, match="S3_BUCKET"):
        _load_adapter("storage", "s3", Settings(s3_bucket=""))
