"""Console email adapter: writes the message to stdout instead of sending."""

import logging
import sys
from typing import TextIO

from app.adapters.email.base import EmailAdapter, EmailMessage
from app.core.config import Settings

logger = logging.getLogger(__name__)


class ConsoleEmailAdapter:
    """Prints each message to ``stream`` (default: current ``sys.stdout``)."""

    def __init__(self, *, email_from: str, stream: TextIO | None = None) -> None:
        self._email_from = email_from
        self._stream = stream

    async def send(self, message: EmailMessage) -> None:
        stream = self._stream if self._stream is not None else sys.stdout
        divider = "-" * 60
        stream.write(
            f"{divider}\n"
            f"From:    {self._email_from}\n"
            f"To:      {message.to}\n"
            f"Subject: {message.subject}\n"
            f"{divider}\n"
            f"{message.text.rstrip()}\n"
            f"{divider}\n"
        )
        stream.flush()
        logger.info("console email to=%s subject=%r", message.to, message.subject)


def create_adapter(settings: Settings) -> EmailAdapter:
    return ConsoleEmailAdapter(email_from=settings.email_from)
