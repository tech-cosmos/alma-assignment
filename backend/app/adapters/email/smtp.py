"""SMTP email adapter for a local relay such as Mailpit (no auth, no TLS)."""

import logging
from email.message import EmailMessage as MimeMessage

import aiosmtplib

from app.adapters.email.base import EmailAdapter, EmailMessage
from app.core.config import Settings

logger = logging.getLogger(__name__)


def build_message(*, email_from: str, message: EmailMessage) -> MimeMessage:
    """Build a text message, upgraded to ``multipart/alternative`` when HTML is present."""
    mime = MimeMessage()
    mime["From"] = email_from
    mime["To"] = message.to
    mime["Subject"] = message.subject
    mime.set_content(message.text)
    if message.html is not None:
        mime.add_alternative(message.html, subtype="html")
    return mime


class SmtpEmailAdapter:
    def __init__(self, *, host: str, port: int, email_from: str, timeout: float = 10.0) -> None:
        self._host = host
        self._port = port
        self._email_from = email_from
        self._timeout = timeout

    async def send(self, message: EmailMessage) -> None:
        mime = build_message(email_from=self._email_from, message=message)
        await aiosmtplib.send(mime, hostname=self._host, port=self._port, timeout=self._timeout)
        logger.info(
            "smtp email sent to=%s subject=%r via %s:%s",
            message.to,
            message.subject,
            self._host,
            self._port,
        )


def create_adapter(settings: Settings) -> EmailAdapter:
    return SmtpEmailAdapter(
        host=settings.smtp_host, port=settings.smtp_port, email_from=settings.email_from
    )
