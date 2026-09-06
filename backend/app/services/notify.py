"""Builds and sends the two lead emails. Never raises: failures are logged."""

import logging

from app.adapters.email.base import EmailAdapter, EmailMessage
from app.core.config import Settings
from app.schemas.lead import LeadRead

log = logging.getLogger(__name__)


class LeadNotifier:
    def __init__(self, email: EmailAdapter, settings: Settings) -> None:
        self._email = email
        self._settings = settings

    def prospect_message(self, lead: LeadRead) -> EmailMessage:
        return EmailMessage(
            to=lead.email,
            subject="We received your information",
            text=(
                f"Hi {lead.first_name},\n\n"
                "Thank you for reaching out. We have received your details and resume, "
                "and an attorney will contact you shortly.\n\n"
                "Best regards,\nThe Alma team"
            ),
        )

    def attorney_message(self, lead: LeadRead) -> EmailMessage:
        link = f"{self._settings.public_web_url.rstrip('/')}/leads/{lead.id}"
        return EmailMessage(
            to=self._settings.attorney_email,
            subject=f"New lead: {lead.first_name} {lead.last_name}",
            text=(
                "A new prospect submitted the intake form.\n\n"
                f"Name: {lead.first_name} {lead.last_name}\n"
                f"Email: {lead.email}\n"
                f"Resume: {lead.resume_name}\n\n"
                f"Review the lead: {link}\n"
            ),
        )

    async def notify_new_lead(self, lead: LeadRead) -> None:
        for message in (self.prospect_message(lead), self.attorney_message(lead)):
            try:
                await self._email.send(message)
            except Exception:
                log.exception("Failed to send '%s' to %s", message.subject, message.to)
