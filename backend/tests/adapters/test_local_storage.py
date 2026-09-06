from __future__ import annotations

from pathlib import Path

import pytest

from app.adapters.storage.base import StorageAdapter
from app.adapters.storage.local import LocalStorageAdapter


@pytest.mark.asyncio
async def test_put_then_open_roundtrip(tmp_path: Path) -> None:
    adapter = LocalStorageAdapter(base_dir=tmp_path)
    await adapter.put("resumes/abc.pdf", b"%PDF-1.4 data", "application/pdf")

    assert (tmp_path / "resumes" / "abc.pdf").read_bytes() == b"%PDF-1.4 data"
    assert await adapter.open("resumes/abc.pdf") == b"%PDF-1.4 data"
    assert not list((tmp_path / "resumes").glob(".*.tmp"))


@pytest.mark.asyncio
async def test_put_overwrites_existing(tmp_path: Path) -> None:
    adapter = LocalStorageAdapter(base_dir=tmp_path)
    await adapter.put("k", b"one", "text/plain")
    await adapter.put("k", b"two", "text/plain")
    assert await adapter.open("k") == b"two"


@pytest.mark.asyncio
async def test_open_missing_raises_file_not_found(tmp_path: Path) -> None:
    adapter = LocalStorageAdapter(base_dir=tmp_path)
    with pytest.raises(FileNotFoundError):
        await adapter.open("resumes/missing.pdf")


@pytest.mark.asyncio
async def test_get_url_returns_api_path(tmp_path: Path) -> None:
    adapter = LocalStorageAdapter(base_dir=tmp_path, url_prefix="/api/v1/storage/")
    assert (
        await adapter.get_url("resumes/a b.pdf") == "/api/v1/storage/resumes/a%20b.pdf"
    )
    assert (
        await adapter.get_url("resumes/a.pdf", expires_in=5)
        == "/api/v1/storage/resumes/a.pdf"
    )


@pytest.mark.parametrize(
    "key", ["", "/etc/passwd", "../outside", "a/../../b", "a\\b", "resumes/../../x"]
)
@pytest.mark.asyncio
async def test_rejects_keys_escaping_base_dir(tmp_path: Path, key: str) -> None:
    adapter = LocalStorageAdapter(base_dir=tmp_path)
    with pytest.raises(ValueError):
        await adapter.put(key, b"x", "text/plain")
    with pytest.raises(ValueError):
        await adapter.open(key)
    with pytest.raises(ValueError):
        await adapter.get_url(key)


@pytest.mark.asyncio
async def test_creates_base_dir_lazily(tmp_path: Path) -> None:
    adapter = LocalStorageAdapter(base_dir=tmp_path / "not" / "yet")
    await adapter.put("k", b"x", "text/plain")
    assert (tmp_path / "not" / "yet" / "k").exists()


def test_local_adapter_satisfies_protocol(tmp_path: Path) -> None:
    assert isinstance(LocalStorageAdapter(base_dir=tmp_path), StorageAdapter)
