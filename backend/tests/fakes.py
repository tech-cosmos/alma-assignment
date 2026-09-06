"""In-memory adapters used by the test suite (Track B ships the real ones)."""

from collections.abc import AsyncIterator

from app.adapters.email.base import EmailMessage


class FakeEmailAdapter:
    def __init__(self, *, fail: bool = False) -> None:
        self.sent: list[EmailMessage] = []
        self.fail = fail

    async def send(self, message: EmailMessage) -> None:
        if self.fail:
            raise RuntimeError("smtp down")
        self.sent.append(message)


class FakeStorageAdapter:
    def __init__(self, *, presign: bool = False) -> None:
        self.objects: dict[str, tuple[bytes, str]] = {}
        self.presign = presign

    async def put(self, key: str, data: bytes, content_type: str) -> None:
        self.objects[key] = (data, content_type)

    async def delete(self, key: str) -> None:
        self.objects.pop(key, None)

    def stream(self, key: str) -> AsyncIterator[bytes]:
        data, _ = self.objects[key]  # KeyError propagates by contract

        async def chunks() -> AsyncIterator[bytes]:
            yield data

        return chunks()

    async def presigned_url(self, key: str, *, expires_in: int) -> str | None:
        if not self.presign:
            return None
        return f"https://signed.example/{key}?expires={expires_in}"
