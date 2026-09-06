"""Amazon SES email adapter (boto3 ``ses.send_email``).

boto3 is synchronous, so the call runs in a worker thread to keep the event
loop free. Credentials come from the standard AWS chain (env vars, profile,
instance role); ``EMAIL_FROM`` must be a verified SES identity.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from typing import Any

import boto3

logger = logging.getLogger(__name__)


class SesEmailAdapter:
    def __init__(
        self, *, region: str, email_from: str, client: Any | None = None
    ) -> None:
        self._email_from = email_from
        self._client = (
            client if client is not None else boto3.client("ses", region_name=region)
        )

    async def send(self, to: str, subject: str, html: str, text: str) -> None:
        send_email: Callable[..., Any] = self._client.send_email
        response = await asyncio.to_thread(
            send_email,
            Source=self._email_from,
            Destination={"ToAddresses": [to]},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {
                    "Text": {"Data": text, "Charset": "UTF-8"},
                    "Html": {"Data": html, "Charset": "UTF-8"},
                },
            },
        )
        logger.info(
            "ses email sent to=%s subject=%r message_id=%s",
            to,
            subject,
            response.get("MessageId"),
        )
