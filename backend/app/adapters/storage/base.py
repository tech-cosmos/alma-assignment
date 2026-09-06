"""Storage adapter contract for resume files.

Keys are opaque, forward-slash separated, relative identifiers chosen by the
caller (e.g. ``resumes/<uuid>.pdf``). They are never raw paths or URLs.

``open`` raises ``FileNotFoundError`` when the key does not exist, for every
implementation, so callers can map it to a 404 uniformly.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class StorageAdapter(Protocol):
    async def put(self, key: str, data: bytes, content_type: str) -> None: ...

    async def get_url(self, key: str, expires_in: int = 900) -> str:
        """URL a client can fetch the object from. For ``local`` this is an API path."""
        ...

    async def open(self, key: str) -> bytes:
        """Read the whole object. Raises ``FileNotFoundError`` if missing."""
        ...
