import io

import pytest

from app.adapters.email.base import EmailAdapter
from app.adapters.email.console import ConsoleEmailAdapter


@pytest.mark.asyncio
async def test_console_adapter_writes_message_to_stream() -> None:
    stream = io.StringIO()
    adapter = ConsoleEmailAdapter(email_from="no-reply@example.com", stream=stream)

    await adapter.send("ada@example.com", "Hello", "<p>hi</p>", "hi")

    out = stream.getvalue()
    assert "From:    no-reply@example.com" in out
    assert "To:      ada@example.com" in out
    assert "Subject: Hello" in out
    assert "\nhi\n" in out
    assert "<p>" not in out  # html body is not dumped to the console


@pytest.mark.asyncio
async def test_console_adapter_defaults_to_stdout(
    capsys: pytest.CaptureFixture[str],
) -> None:
    adapter = ConsoleEmailAdapter(email_from="no-reply@example.com")
    await adapter.send("ada@example.com", "Subj", "<p>x</p>", "body text")
    assert "body text" in capsys.readouterr().out


def test_console_adapter_satisfies_protocol() -> None:
    assert isinstance(ConsoleEmailAdapter(email_from="x@y.z"), EmailAdapter)
