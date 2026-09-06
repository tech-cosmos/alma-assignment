"""Builds and sends the two lead emails. Never raises: failures are logged."""

import logging

from app.adapters.email.base import EmailAdapter, EmailMessage
from app.adapters.email.templates import (
    render_attorney_notification,
    render_prospect_confirmation,
)
from app.core.config import Settings
from app.schemas.lead import LeadRead

log = logging.getLogger(__name__)


class LeadNotifier:
    def __init__(self, email: EmailAdapter, settings: Settings) -> None:
        self._email = email
        self._settings = settings

    def prospect_message(self, lead: LeadRead) -> EmailMessage:
        rendered = render_prospect_confirmation(
            first_name=lead.first_name, last_name=lead.last_name
        )
        return EmailMessage(
            to=lead.email, subject=rendered.subject, text=rendered.text, html=rendered.html
        )

    def attorney_message(self, lead: LeadRead) -> EmailMessage:
        rendered = render_attorney_notification(
            lead_id=str(lead.id),
            first_name=lead.first_name,
            last_name=lead.last_name,
            email=lead.email,
            resume_name=lead.resume_name,
            public_web_url=self._settings.public_web_url,
            submitted_at=lead.created_at,
        )
        return EmailMessage(
            to=self._settings.attorney_email,
            subject=rendered.subject,
            text=rendered.text,
            html=rendered.html,
        )

    async def notify_new_lead(self, lead: LeadRead) -> None:
        for message in (self.prospect_message(lead), self.attorney_message(lead)):
            try:
                await self._email.send(message)
            except Exception:
                log.exception("Failed to send '%s' to %s", message.subject, message.to)
