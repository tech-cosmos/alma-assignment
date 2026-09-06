import pytest

from app.adapters.email.base import EmailAdapter
from app.adapters.storage.base import StorageAdapter
from tests.fakes import FakeEmailAdapter, FakeStorageAdapter, SentEmail, StoredObject


@pytest.mark.asyncio
async def test_fake_email_records_sends() -> None:
    fake = FakeEmailAdapter()
    await fake.send("a@x.io", "s", "<p>h</p>", "t")
    assert fake.sent == [SentEmail(to="a@x.io", subject="s", html="<p>h</p>", text="t")]
    assert fake.sent_to("a@x.io") == fake.sent
    assert fake.sent_to("nobody@x.io") == []
    fake.reset()
    assert fake.sent == []


@pytest.mark.asyncio
async def test_fake_email_can_fail() -> None:
    fake = FakeEmailAdapter(fail=RuntimeError("smtp down"))
    with pytest.raises(RuntimeError, match="smtp down"):
        await fake.send("a@x.io", "s", "h", "t")
    assert fake.sent == []


@pytest.mark.asyncio
async def test_fake_storage_roundtrip_and_calls() -> None:
    fake = FakeStorageAdapter()
    await fake.put("k", b"d", "application/pdf")
    assert fake.objects["k"] == StoredObject(data=b"d", content_type="application/pdf")
    assert await fake.open("k") == b"d"
    assert await fake.get_url("k", expires_in=5) == "fake://storage/k?expires_in=5"
    assert fake.calls == [("put", "k"), ("open", "k"), ("get_url", "k")]
    with pytest.raises(FileNotFoundError):
        await fake.open("missing")


def test_fakes_satisfy_protocols() -> None:
    assert isinstance(FakeEmailAdapter(), EmailAdapter)
    assert isinstance(FakeStorageAdapter(), StorageAdapter)
