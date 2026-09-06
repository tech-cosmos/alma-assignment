"""Email adapters. ``app.api.deps`` selects one by ``EMAIL_PROVIDER`` and calls the
provider module's ``create_adapter(settings)``."""

from .base import EmailAdapter, EmailMessage
from .templates import (
    RenderedEmail,
    lead_page_url,
    render_attorney_notification,
    render_prospect_confirmation,
)

EMAIL_PROVIDERS = ("console", "smtp", "ses")

__all__ = [
    "EMAIL_PROVIDERS",
    "EmailAdapter",
    "EmailMessage",
    "RenderedEmail",
    "lead_page_url",
    "render_attorney_notification",
    "render_prospect_confirmation",
]
