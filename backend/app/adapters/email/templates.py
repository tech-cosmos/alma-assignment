"""The two transactional emails sent on lead submission.

Plain f-string templates. Every user-supplied value is HTML-escaped before
interpolation into the HTML body; the text body is left as-is because it is
sent as ``text/plain``.

The attorney notification links to the internal lead page and deliberately
does NOT include the resume (see ``docs/PLAN.md`` section 5).
"""

from __future__ import annotations

from dataclasses import dataclass
from html import escape


@dataclass(frozen=True, slots=True)
class RenderedEmail:
    subject: str
    html: str
    text: str


def render_prospect_confirmation(*, first_name: str, last_name: str) -> RenderedEmail:
    """Confirmation sent to the prospect after their submission is stored."""
    full_name = f"{first_name} {last_name}".strip()
    subject = "We received your information"
    text = (
        f"Hi {full_name},\n"
        "\n"
        "Thank you for reaching out. We have received your details and your resume.\n"
        "An attorney will review your information and contact you shortly.\n"
        "\n"
        "You do not need to do anything else right now.\n"
        "\n"
        "Kind regards,\n"
        "The Alma team\n"
    )
    html = (
        '<!doctype html><html><body style="font-family:sans-serif;line-height:1.5">'
        f"<p>Hi {escape(full_name)},</p>"
        "<p>Thank you for reaching out. We have received your details and your resume. "
        "An attorney will review your information and contact you shortly.</p>"
        "<p>You do not need to do anything else right now.</p>"
        "<p>Kind regards,<br>The Alma team</p>"
        "</body></html>"
    )
    return RenderedEmail(subject=subject, html=html, text=text)


def lead_page_url(public_web_url: str, lead_id: str) -> str:
    """Absolute URL of the internal lead page: ``PUBLIC_WEB_URL/leads/{id}``."""
    return f"{public_web_url.rstrip('/')}/leads/{lead_id}"


def render_attorney_notification(
    *,
    lead_id: str,
    first_name: str,
    last_name: str,
    email: str,
    resume_name: str,
    public_web_url: str,
) -> RenderedEmail:
    """Notification to the attorney. Links to the lead; never attaches the resume."""
    full_name = f"{first_name} {last_name}".strip()
    url = lead_page_url(public_web_url, lead_id)
    subject = f"New lead: {full_name}"
    text = (
        "A new lead was submitted.\n"
        "\n"
        f"Name:   {full_name}\n"
        f"Email:  {email}\n"
        f"Resume: {resume_name}\n"
        "\n"
        f"View the lead and download the resume here:\n{url}\n"
    )
    html = (
        '<!doctype html><html><body style="font-family:sans-serif;line-height:1.5">'
        "<p>A new lead was submitted.</p>"
        '<table cellpadding="4">'
        f"<tr><td><strong>Name</strong></td><td>{escape(full_name)}</td></tr>"
        f"<tr><td><strong>Email</strong></td><td>{escape(email)}</td></tr>"
        f"<tr><td><strong>Resume</strong></td><td>{escape(resume_name)}</td></tr>"
        "</table>"
        f'<p><a href="{escape(url, quote=True)}">View lead</a> '
        "to see the details and download the resume.</p>"
        "</body></html>"
    )
    return RenderedEmail(subject=subject, html=html, text=text)
