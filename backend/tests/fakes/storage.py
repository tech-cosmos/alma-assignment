from collections.abc import AsyncIterator


class FakeStorageAdapter:
    """Keeps objects in a dict and records every call.

    ``presign=True`` makes ``presigned_url`` return a URL (S3-like); the default
    returns ``None`` (local-disk-like) so the API streams the object.
    """

    def __init__(self, *, presign: bool = False) -> None:
        self.objects: dict[str, tuple[bytes, str]] = {}
        self.calls: list[tuple[str, str]] = []
        self.presign = presign

    async def put(self, key: str, data: bytes, content_type: str) -> None:
        self.calls.append(("put", key))
        self.objects[key] = (data, content_type)

    async def delete(self, key: str) -> None:
        self.calls.append(("delete", key))
        self.objects.pop(key, None)

    async def stream(self, key: str) -> AsyncIterator[bytes]:
        self.calls.append(("stream", key))
        data, _ = self.objects[key]  # KeyError propagates by contract

        async def chunks() -> AsyncIterator[bytes]:
            yield data

        return chunks()

    async def presigned_url(self, key: str, *, expires_in: int) -> str | None:
        self.calls.append(("presigned_url", key))
        if not self.presign:
            return None
        return f"https://signed.example/{key}?expires={expires_in}"

    def reset(self) -> None:
        self.objects.clear()
        self.calls.clear()
