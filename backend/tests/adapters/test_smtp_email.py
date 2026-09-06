"""Sends through a real in-process SMTP server (aiosmtpd) with no auth or TLS,
the same shape as Mailpit."""

from __future__ import annotations

import asyncio
import socket
from collections.abc import Iterator
from email.message import Message

import aiosmtplib
import pytest
from aiosmtpd.controller import Controller
from aiosmtpd.handlers import Message as MessageHandler

from app.adapters.email.base import EmailAdapter
from app.adapters.email.smtp import SmtpEmailAdapter, build_message


class _Inbox(MessageHandler):
    """Collects delivered messages; envelope data lands in X-MailFrom/X-RcptTo."""

    def __init__(self) -> None:
        super().__init__()
        self.messages: list[Message] = []

    def handle_message(self, message: Message) -> None:
        self.messages.append(message)


@pytest.fixture
def smtp_server() -> Iterator[tuple[_Inbox, str, int]]:
    inbox = _Inbox()
    with socket.socket() as probe:  # aiosmtpd cannot bind port 0 itself
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    controller = Controller(inbox, hostname="127.0.0.1", port=port)
    controller.start()
    try:
        yield inbox, controller.hostname, controller.port
    finally:
        controller.stop()


@pytest.mark.asyncio
async def test_smtp_adapter_delivers_multipart_message(
    smtp_server: tuple[_Inbox, str, int],
) -> None:
    inbox, host, port = smtp_server
    adapter = SmtpEmailAdapter(host=host, port=port, email_from="no-reply@example.com")

    await adapter.send("ada@example.com", "Hello Ada", "<p>Hi <b>Ada</b></p>", "Hi Ada")

    (msg,) = inbox.messages
    assert msg["X-MailFrom"] == "no-reply@example.com"
    assert msg["X-RcptTo"] == "ada@example.com"
    assert msg["From"] == "no-reply@example.com"
    assert msg["To"] == "ada@example.com"
    assert msg["Subject"] == "Hello Ada"
    assert msg.get_content_type() == "multipart/alternative"
    parts = {
        p.get_content_type(): p.get_payload(decode=True)
        for p in msg.walk()
        if not p.is_multipart()
    }
    assert parts["text/plain"].strip() == b"Hi Ada"
    assert parts["text/html"].strip() == b"<p>Hi <b>Ada</b></p>"


@pytest.mark.asyncio
async def test_smtp_adapter_raises_when_server_unreachable() -> None:
    # Bind a port then close it so nothing is listening there.
    server = await asyncio.start_server(lambda r, w: None, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    server.close()
    await server.wait_closed()

    adapter = SmtpEmailAdapter(
        host="127.0.0.1", port=port, email_from="no-reply@example.com", timeout=2
    )
    with pytest.raises(aiosmtplib.SMTPException):
        await adapter.send("ada@example.com", "x", "<p>x</p>", "x")


def test_build_message_has_text_and_html_alternatives() -> None:
    msg = build_message(
        email_from="a@b.c", to="d@e.f", subject="s", html="<i>h</i>", text="t"
    )
    assert msg.get_content_type() == "multipart/alternative"
    assert [p.get_content_type() for p in msg.iter_parts()] == [
        "text/plain",
        "text/html",
    ]


def test_smtp_adapter_satisfies_protocol() -> None:
    assert isinstance(
        SmtpEmailAdapter(host="h", port=1, email_from="x@y.z"), EmailAdapter
    )
