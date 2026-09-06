"""Local-disk storage adapter (default for ``docker compose up``).

Files are written under ``base_dir``. There is nothing to sign, so
``presigned_url`` returns ``None`` and the API streams the object instead.
Keys are validated to stay inside ``base_dir``.
"""

import asyncio
import os
from collections.abc import AsyncIterator
from pathlib import Path

from app.adapters.storage.base import StorageAdapter
from app.core.config import Settings

CHUNK_SIZE = 64 * 1024


class LocalStorageAdapter:
    def __init__(self, *, base_dir: str | os.PathLike[str]) -> None:
        self._base_dir = Path(base_dir).resolve()

    @property
    def base_dir(self) -> Path:
        return self._base_dir

    def _path_for(self, key: str) -> Path:
        if not key or key.startswith("/") or "\\" in key or ".." in key.split("/"):
            raise ValueError(f"Invalid storage key {key!r}")
        path = (self._base_dir / key).resolve()
        if self._base_dir != path and self._base_dir not in path.parents:
            raise ValueError(f"Invalid storage key {key!r}")
        return path

    async def put(self, key: str, data: bytes, content_type: str) -> None:
        path = self._path_for(key)
        await asyncio.to_thread(self._write, path, data)

    @staticmethod
    def _write(path: Path, data: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(f".{path.name}.tmp")
        tmp.write_bytes(data)
        os.replace(tmp, path)

    async def delete(self, key: str) -> None:
        path = self._path_for(key)
        await asyncio.to_thread(self._unlink, path)

    @staticmethod
    def _unlink(path: Path) -> None:
        path.unlink(missing_ok=True)

    async def stream(self, key: str) -> AsyncIterator[bytes]:
        path = self._path_for(key)
        if not await asyncio.to_thread(path.is_file):
            raise KeyError(key)

        async def chunks() -> AsyncIterator[bytes]:
            with path.open("rb") as fh:
                while chunk := await asyncio.to_thread(fh.read, CHUNK_SIZE):
                    yield chunk

        return chunks()

    async def presigned_url(self, key: str, *, expires_in: int) -> str | None:
        self._path_for(key)
        return None


def create_adapter(settings: Settings) -> StorageAdapter:
    return LocalStorageAdapter(base_dir=settings.storage_local_dir)
