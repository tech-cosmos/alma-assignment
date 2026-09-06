"""Amazon SES email adapter (boto3 ``ses.send_email``).

boto3 is synchronous, so the call runs in a worker thread to keep the event
loop free. Credentials come from the standard AWS chain (env vars, profile,
instance role); ``EMAIL_FROM`` must be a verified SES identity.
"""

import asyncio
import logging
from collections.abc import Callable
from typing import Any

import boto3

from app.adapters.email.base import EmailAdapter, EmailMessage
from app.core.config import Settings

logger = logging.getLogger(__name__)


class SesEmailAdapter:
    def __init__(self, *, region: str, email_from: str, client: Any | None = None) -> None:
        self._email_from = email_from
        self._client = client if client is not None else boto3.client("ses", region_name=region)

    async def send(self, message: EmailMessage) -> None:
        send_email: Callable[..., Any] = self._client.send_email
        body: dict[str, dict[str, str]] = {"Text": {"Data": message.text, "Charset": "UTF-8"}}
        if message.html is not None:
            body["Html"] = {"Data": message.html, "Charset": "UTF-8"}
        response = await asyncio.to_thread(
            send_email,
            Source=self._email_from,
            Destination={"ToAddresses": [message.to]},
            Message={"Subject": {"Data": message.subject, "Charset": "UTF-8"}, "Body": body},
        )
        logger.info(
            "ses email sent to=%s subject=%r message_id=%s",
            message.to,
            message.subject,
            response.get("MessageId"),
        )


def create_adapter(settings: Settings) -> EmailAdapter:
    return SesEmailAdapter(region=settings.aws_region, email_from=settings.email_from)
