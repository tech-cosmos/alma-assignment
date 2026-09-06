import io

import pytest

from app.adapters.email.base import EmailAdapter, EmailMessage
from app.adapters.email.console import ConsoleEmailAdapter

MSG = EmailMessage(to="ada@example.com", subject="Hello", text="hi", html="<p>hi</p>")


async def test_console_adapter_writes_message_to_stream() -> None:
    stream = io.StringIO()
    adapter = ConsoleEmailAdapter(email_from="no-reply@example.com", stream=stream)

    await adapter.send(MSG)

    out = stream.getvalue()
    assert "From:    no-reply@example.com" in out
    assert "To:      ada@example.com" in out
    assert "Subject: Hello" in out
    assert "\nhi\n" in out
    assert "<p>" not in out  # html body is not dumped to the console


async def test_console_adapter_defaults_to_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    adapter = ConsoleEmailAdapter(email_from="no-reply@example.com")
    await adapter.send(EmailMessage(to="ada@example.com", subject="Subj", text="body text"))
    assert "body text" in capsys.readouterr().out


def test_console_adapter_satisfies_protocol() -> None:
    assert isinstance(ConsoleEmailAdapter(email_from="x@y.z"), EmailAdapter)
