"""Email adapters. Select one with ``build_email_adapter``."""

from __future__ import annotations

from .base import EmailAdapter
from .console import ConsoleEmailAdapter
from .ses import SesEmailAdapter
from .smtp import SmtpEmailAdapter
from .templates import (
    RenderedEmail,
    lead_page_url,
    render_attorney_notification,
    render_prospect_confirmation,
)

EMAIL_PROVIDERS = ("console", "smtp", "ses")


def build_email_adapter(
    provider: str,
    *,
    email_from: str,
    smtp_host: str = "localhost",
    smtp_port: int = 1025,
    aws_region: str = "us-east-1",
) -> EmailAdapter:
    """Return the adapter named by ``EMAIL_PROVIDER``: console, smtp or ses."""
    match provider:
        case "console":
            return ConsoleEmailAdapter(email_from=email_from)
        case "smtp":
            return SmtpEmailAdapter(
                host=smtp_host, port=smtp_port, email_from=email_from
            )
        case "ses":
            return SesEmailAdapter(region=aws_region, email_from=email_from)
        case _:
            raise ValueError(
                f"Unknown EMAIL_PROVIDER {provider!r}; expected {EMAIL_PROVIDERS}"
            )


__all__ = [
    "EMAIL_PROVIDERS",
    "ConsoleEmailAdapter",
    "EmailAdapter",
    "RenderedEmail",
    "SesEmailAdapter",
    "SmtpEmailAdapter",
    "build_email_adapter",
    "lead_page_url",
    "render_attorney_notification",
    "render_prospect_confirmation",
]
