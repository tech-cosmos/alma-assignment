"""SMTP email adapter for a local relay such as Mailpit (no auth, no TLS)."""

from __future__ import annotations

import logging
from email.message import EmailMessage

import aiosmtplib

logger = logging.getLogger(__name__)


def build_message(
    *, email_from: str, to: str, subject: str, html: str, text: str
) -> EmailMessage:
    """Build a ``multipart/alternative`` message with text and HTML parts."""
    message = EmailMessage()
    message["From"] = email_from
    message["To"] = to
    message["Subject"] = subject
    message.set_content(text)
    message.add_alternative(html, subtype="html")
    return message


class SmtpEmailAdapter:
    def __init__(
        self, *, host: str, port: int, email_from: str, timeout: float = 10.0
    ) -> None:
        self._host = host
        self._port = port
        self._email_from = email_from
        self._timeout = timeout

    async def send(self, to: str, subject: str, html: str, text: str) -> None:
        message = build_message(
            email_from=self._email_from, to=to, subject=subject, html=html, text=text
        )
        await aiosmtplib.send(
            message,
            hostname=self._host,
            port=self._port,
            timeout=self._timeout,
        )
        logger.info(
            "smtp email sent to=%s subject=%r via %s:%s",
            to,
            subject,
            self._host,
            self._port,
        )
