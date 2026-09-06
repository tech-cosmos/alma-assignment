"""Local-disk storage adapter (default for ``docker compose up``).

Files are written under ``base_dir``. ``get_url`` cannot sign anything, so it
returns an API path (``{url_prefix}/{key}``) that the API serves by streaming
``open(key)``. Keys are validated to stay inside ``base_dir``.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from urllib.parse import quote


class LocalStorageAdapter:
    def __init__(
        self, *, base_dir: str | os.PathLike[str], url_prefix: str = "/api/v1/storage"
    ) -> None:
        self._base_dir = Path(base_dir).resolve()
        self._url_prefix = url_prefix.rstrip("/")

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

    async def get_url(self, key: str, expires_in: int = 900) -> str:
        self._path_for(key)
        return f"{self._url_prefix}/{quote(key)}"

    async def open(self, key: str) -> bytes:
        path = self._path_for(key)
        try:
            return await asyncio.to_thread(path.read_bytes)
        except FileNotFoundError:
            raise FileNotFoundError(key) from None
