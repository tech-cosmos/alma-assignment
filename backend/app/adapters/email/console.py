"""Console email adapter: writes the message to stdout instead of sending."""

from __future__ import annotations

import logging
import sys
from typing import TextIO

logger = logging.getLogger(__name__)


class ConsoleEmailAdapter:
    """Prints each message to ``stream`` (default: current ``sys.stdout``)."""

    def __init__(self, *, email_from: str, stream: TextIO | None = None) -> None:
        self._email_from = email_from
        self._stream = stream

    async def send(self, to: str, subject: str, html: str, text: str) -> None:
        stream = self._stream if self._stream is not None else sys.stdout
        divider = "-" * 60
        stream.write(
            f"{divider}\n"
            f"From:    {self._email_from}\n"
            f"To:      {to}\n"
            f"Subject: {subject}\n"
            f"{divider}\n"
            f"{text.rstrip()}\n"
            f"{divider}\n"
        )
        stream.flush()
        logger.info("console email to=%s subject=%r", to, subject)
