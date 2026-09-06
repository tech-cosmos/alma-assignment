from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import boto3
import pytest
from botocore.exceptions import ClientError
from moto import mock_aws

from app.adapters.email.base import EmailAdapter
from app.adapters.email.ses import SesEmailAdapter

REGION = "us-east-1"


@pytest.fixture
def aws_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", REGION)
    with mock_aws():
        yield


@pytest.mark.asyncio
async def test_ses_adapter_sends_from_verified_identity(aws_env: None) -> None:
    ses = boto3.client("ses", region_name=REGION)
    ses.verify_email_identity(EmailAddress="no-reply@example.com")
    adapter = SesEmailAdapter(region=REGION, email_from="no-reply@example.com")

    await adapter.send("ada@example.com", "Hello", "<p>hi</p>", "hi")

    quota = ses.get_send_quota()
    assert quota["SentLast24Hours"] == 1


@pytest.mark.asyncio
async def test_ses_adapter_raises_for_unverified_sender(aws_env: None) -> None:
    adapter = SesEmailAdapter(region=REGION, email_from="nobody@example.com")
    with pytest.raises(ClientError):
        await adapter.send("ada@example.com", "Hello", "<p>hi</p>", "hi")


@pytest.mark.asyncio
async def test_ses_adapter_passes_both_bodies_to_injected_client() -> None:
    calls: list[dict[str, Any]] = []

    class StubClient:
        def send_email(self, **kwargs: Any) -> dict[str, str]:
            calls.append(kwargs)
            return {"MessageId": "m-1"}

    adapter = SesEmailAdapter(
        region=REGION, email_from="no-reply@example.com", client=StubClient()
    )
    await adapter.send("ada@example.com", "Subj", "<p>h</p>", "t")

    (call,) = calls
    assert call["Source"] == "no-reply@example.com"
    assert call["Destination"] == {"ToAddresses": ["ada@example.com"]}
    assert call["Message"]["Subject"]["Data"] == "Subj"
    assert call["Message"]["Body"]["Html"]["Data"] == "<p>h</p>"
    assert call["Message"]["Body"]["Text"]["Data"] == "t"


def test_ses_adapter_satisfies_protocol() -> None:
    assert isinstance(
        SesEmailAdapter(region=REGION, email_from="x@y.z", client=object()),
        EmailAdapter,
    )
