from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from app.adapters.storage.base import StorageAdapter
from app.adapters.storage.local import LocalStorageAdapter


async def _read_all(chunks: AsyncIterator[bytes]) -> bytes:
    return b"".join([chunk async for chunk in chunks])


async def test_put_then_stream_roundtrip(tmp_path: Path) -> None:
    adapter = LocalStorageAdapter(base_dir=tmp_path)
    await adapter.put("resumes/abc.pdf", b"%PDF-1.4 data", "application/pdf")

    assert (tmp_path / "resumes" / "abc.pdf").read_bytes() == b"%PDF-1.4 data"
    assert await _read_all(await adapter.stream("resumes/abc.pdf")) == b"%PDF-1.4 data"
    assert not list((tmp_path / "resumes").glob(".*.tmp"))


async def test_put_overwrites_existing(tmp_path: Path) -> None:
    adapter = LocalStorageAdapter(base_dir=tmp_path)
    await adapter.put("k", b"one", "text/plain")
    await adapter.put("k", b"two", "text/plain")
    assert await _read_all(await adapter.stream("k")) == b"two"


async def test_stream_missing_raises_key_error(tmp_path: Path) -> None:
    adapter = LocalStorageAdapter(base_dir=tmp_path)
    with pytest.raises(KeyError):
        await adapter.stream("resumes/missing.pdf")


async def test_delete_removes_file_and_tolerates_missing(tmp_path: Path) -> None:
    adapter = LocalStorageAdapter(base_dir=tmp_path)
    await adapter.put("k", b"x", "text/plain")
    await adapter.delete("k")
    assert not (tmp_path / "k").exists()
    await adapter.delete("k")  # no raise


async def test_presigned_url_is_none_for_local_disk(tmp_path: Path) -> None:
    adapter = LocalStorageAdapter(base_dir=tmp_path)
    assert await adapter.presigned_url("resumes/a.pdf", expires_in=5) is None


@pytest.mark.parametrize(
    "key", ["", "/etc/passwd", "../outside", "a/../../b", "a\\b", "resumes/../../x"]
)
async def test_rejects_keys_escaping_base_dir(tmp_path: Path, key: str) -> None:
    adapter = LocalStorageAdapter(base_dir=tmp_path)
    with pytest.raises(ValueError):
        await adapter.put(key, b"x", "text/plain")
    with pytest.raises(ValueError):
        await adapter.stream(key)
    with pytest.raises(ValueError):
        await adapter.delete(key)
    with pytest.raises(ValueError):
        await adapter.presigned_url(key, expires_in=5)


async def test_creates_base_dir_lazily(tmp_path: Path) -> None:
    adapter = LocalStorageAdapter(base_dir=tmp_path / "not" / "yet")
    await adapter.put("k", b"x", "text/plain")
    assert (tmp_path / "not" / "yet" / "k").exists()


def test_local_adapter_satisfies_protocol(tmp_path: Path) -> None:
    assert isinstance(LocalStorageAdapter(base_dir=tmp_path), StorageAdapter)
