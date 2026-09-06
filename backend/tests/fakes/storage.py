from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StoredObject:
    data: bytes
    content_type: str


class FakeStorageAdapter:
    """Keeps objects in a dict and records every call."""

    def __init__(self, *, url_prefix: str = "fake://storage") -> None:
        self.objects: dict[str, StoredObject] = {}
        self.calls: list[tuple[str, str]] = []
        self._url_prefix = url_prefix.rstrip("/")

    async def put(self, key: str, data: bytes, content_type: str) -> None:
        self.calls.append(("put", key))
        self.objects[key] = StoredObject(data=data, content_type=content_type)

    async def get_url(self, key: str, expires_in: int = 900) -> str:
        self.calls.append(("get_url", key))
        return f"{self._url_prefix}/{key}?expires_in={expires_in}"

    async def open(self, key: str) -> bytes:
        self.calls.append(("open", key))
        try:
            return self.objects[key].data
        except KeyError:
            raise FileNotFoundError(key) from None

    def reset(self) -> None:
        self.objects.clear()
        self.calls.clear()
