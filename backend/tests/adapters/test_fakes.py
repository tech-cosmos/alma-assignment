import pytest

from app.adapters.email.base import EmailAdapter, EmailMessage
from app.adapters.storage.base import StorageAdapter
from tests.fakes import FakeEmailAdapter, FakeStorageAdapter

MSG = EmailMessage(to="a@x.io", subject="s", text="t", html="<p>h</p>")


async def test_fake_email_records_sends() -> None:
    fake = FakeEmailAdapter()
    await fake.send(MSG)
    assert fake.sent == [MSG]
    assert fake.sent_to("a@x.io") == fake.sent
    assert fake.sent_to("nobody@x.io") == []
    fake.reset()
    assert fake.sent == []


async def test_fake_email_can_fail() -> None:
    fake = FakeEmailAdapter(fail=True)
    with pytest.raises(RuntimeError, match="smtp down"):
        await fake.send(MSG)
    assert fake.sent == []


async def test_fake_storage_roundtrip_and_calls() -> None:
    fake = FakeStorageAdapter()
    await fake.put("k", b"d", "application/pdf")
    assert fake.objects["k"] == (b"d", "application/pdf")
    assert b"".join([c async for c in await fake.stream("k")]) == b"d"
    assert await fake.presigned_url("k", expires_in=5) is None
    assert fake.calls == [("put", "k"), ("stream", "k"), ("presigned_url", "k")]
    with pytest.raises(KeyError):
        await fake.stream("missing")
    await fake.delete("k")
    assert "k" not in fake.objects


async def test_fake_storage_can_presign() -> None:
    fake = FakeStorageAdapter(presign=True)
    assert await fake.presigned_url("k", expires_in=5) == "https://signed.example/k?expires=5"


def test_fakes_satisfy_protocols() -> None:
    assert isinstance(FakeEmailAdapter(), EmailAdapter)
    assert isinstance(FakeStorageAdapter(), StorageAdapter)
