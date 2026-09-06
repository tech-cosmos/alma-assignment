"""The two transactional emails sent on lead submission.

Plain f-string templates. Every user-supplied value is HTML-escaped before
interpolation into the HTML body; the text body is left as-is because it is
sent as ``text/plain``.

The HTML is written for email clients, not browsers: table layout, every
style inline, explicit background and text colour on every block (so Gmail,
Outlook and Apple Mail dark mode cannot invert it into mush), a system font
stack, no web fonts, no scripts, no images and no tracking pixels. The
header carries a text wordmark instead of a logo. The palette mirrors the
web app (``frontend/app/globals.css``): warm paper, deep ink green, brass.

The attorney notification links to the internal lead page and deliberately
does NOT include the resume (see ``docs/PLAN.md`` section 5).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from html import escape

FIRM_NAME = "Alma Immigration"
# Same wording (and en dash) as the public form in frontend/app/page.tsx.
PRIVILEGE_NOTICE = "Attorney–client privilege does not attach until an engagement letter is signed."  # noqa: RUF001

# Brand palette, converted to sRGB hex from the oklch values in globals.css.
_PAPER = "#F7F3EB"
_CARD = "#FEFCF7"
_INK = "#132C24"
_INK_FG = "#F7F3EB"
_BRASS = "#C38C37"
_BRASS_FG = "#251804"
_TEXT = "#121E18"
_MUTED = "#5C675D"
_BORDER = "#D6D0C5"

_FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"
_BODY_STYLE = f"font-family:{_FONT};font-size:16px;line-height:24px;color:{_TEXT};"
_MUTED_STYLE = f"font-family:{_FONT};font-size:13px;line-height:20px;color:{_MUTED};"


@dataclass(frozen=True, slots=True)
class RenderedEmail:
    subject: str
    html: str
    text: str


def _layout(*, title: str, preheader: str, body: str) -> str:
    """Wrap ``body`` (table rows) in the shared shell: header, card, footer.

    ``title`` and ``preheader`` must already be escaped by the caller.
    """
    return (
        "<!doctype html>"
        '<html lang="en">'
        "<head>"
        '<meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta name="color-scheme" content="light">'
        '<meta name="supported-color-schemes" content="light">'
        f"<title>{title}</title>"
        "</head>"
        f'<body style="margin:0;padding:0;background-color:{_PAPER};" bgcolor="{_PAPER}">'
        # Preheader: shown in the inbox preview, hidden in the body.
        '<div style="display:none;max-height:0;overflow:hidden;font-size:1px;'
        f'line-height:1px;color:{_PAPER};">{preheader}</div>'
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
        f'style="background-color:{_PAPER};" bgcolor="{_PAPER}">'
        "<tr>"
        f'<td align="center" style="padding:32px 16px;background-color:{_PAPER};" '
        f'bgcolor="{_PAPER}">'
        "<!--[if mso]>"
        '<table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0">'
        "<tr><td>"
        "<![endif]-->"
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
        f'style="max-width:600px;background-color:{_CARD};border:1px solid {_BORDER};" '
        f'bgcolor="{_CARD}">'
        # Header: ink band with the text wordmark and a brass rule beneath it.
        "<tr>"
        f'<td align="left" style="padding:24px 32px 20px;background-color:{_INK};" '
        f'bgcolor="{_INK}">'
        f'<span style="font-family:{_FONT};font-size:20px;line-height:24px;'
        f"font-weight:600;letter-spacing:0.04em;color:{_INK_FG};"
        f'text-decoration:none;">{escape(FIRM_NAME)}</span>'
        "</td>"
        "</tr>"
        "<tr>"
        f'<td style="height:4px;font-size:4px;line-height:4px;background-color:{_BRASS};" '
        f'bgcolor="{_BRASS}">&nbsp;</td>'
        "</tr>"
        # Body rows supplied by the caller.
        f"{body}"
        # Footer.
        "<tr>"
        f'<td style="padding:20px 32px;background-color:{_PAPER};border-top:1px solid {_BORDER};" '
        f'bgcolor="{_PAPER}">'
        f'<p style="margin:0;{_MUTED_STYLE}">{escape(FIRM_NAME)}</p>'
        "</td>"
        "</tr>"
        "</table>"
        "<!--[if mso]>"
        "</td></tr></table>"
        "<![endif]-->"
        "</td>"
        "</tr>"
        "</table>"
        "</body>"
        "</html>"
    )


def _content_row(inner: str, *, padding: str = "0 32px") -> str:
    return (
        "<tr>"
        f'<td style="padding:{padding};background-color:{_CARD};" bgcolor="{_CARD}">'
        f"{inner}"
        "</td>"
        "</tr>"
    )


def _step_row(number: int, heading: str, detail: str) -> str:
    """One numbered step: a brass badge beside a bold heading and a short line."""
    return (
        "<tr>"
        f'<td width="36" valign="top" style="padding:0 12px 16px 0;background-color:{_CARD};" '
        f'bgcolor="{_CARD}">'
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0">'
        "<tr>"
        f'<td align="center" width="28" height="28" style="width:28px;height:28px;'
        f"border-radius:14px;background-color:{_BRASS};font-family:{_FONT};font-size:13px;"
        f'line-height:28px;font-weight:700;color:{_BRASS_FG};" bgcolor="{_BRASS}">'
        f"{number}</td>"
        "</tr>"
        "</table>"
        "</td>"
        f'<td valign="top" style="padding:0 0 16px;background-color:{_CARD};" bgcolor="{_CARD}">'
        f'<p style="margin:0;{_BODY_STYLE}font-weight:600;">{heading}</p>'
        f'<p style="margin:2px 0 0;{_BODY_STYLE}font-size:15px;line-height:22px;'
        f'color:{_MUTED};">{detail}</p>'
        "</td>"
        "</tr>"
    )


def render_prospect_confirmation(*, first_name: str, last_name: str) -> RenderedEmail:
    """Confirmation sent to the prospect after their submission is stored."""
    full_name = f"{first_name} {last_name}".strip()
    subject = "We received your information"
    text = (
        f"Hi {full_name},\n"
        "\n"
        f"Thank you for contacting {FIRM_NAME}. We have received your information\n"
        "and your resume.\n"
        "\n"
        "What happens next:\n"
        "\n"
        "1. We review your background.\n"
        "   An attorney on our team will read through the details you shared.\n"
        "\n"
        "2. An attorney reaches out.\n"
        "   You will hear from us directly, usually within a few business days.\n"
        "\n"
        "3. You do nothing for now.\n"
        "   There is nothing further to send or sign at this stage.\n"
        "\n"
        f"{PRIVILEGE_NOTICE}\n"
        "\n"
        "Kind regards,\n"
        f"{FIRM_NAME}\n"
    )
    safe_name = escape(full_name)
    body = (
        _content_row(
            f'<p style="margin:0 0 12px;{_BODY_STYLE}font-size:22px;line-height:30px;'
            f'font-weight:600;color:{_INK};">Hi {safe_name},</p>'
            f'<p style="margin:0 0 20px;{_BODY_STYLE}">Thank you for contacting '
            f"{escape(FIRM_NAME)}. We have received your information and your resume.</p>"
            f'<p style="margin:0 0 12px;{_MUTED_STYLE}text-transform:uppercase;'
            'letter-spacing:0.12em;font-size:12px;font-weight:600;">What happens next</p>',
            padding="32px 32px 0",
        )
        + _content_row(
            '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
            f'border="0" style="background-color:{_CARD};" bgcolor="{_CARD}">'
            + _step_row(
                1,
                "We review your background.",
                "An attorney on our team will read through the details you shared.",
            )
            + _step_row(
                2,
                "An attorney reaches out.",
                "You will hear from us directly, usually within a few business days.",
            )
            + _step_row(
                3,
                "You do nothing for now.",
                "There is nothing further to send or sign at this stage.",
            )
            + "</table>"
        )
        + _content_row(
            f'<p style="margin:0;padding:16px 0 0;border-top:1px solid {_BORDER};'
            f'{_MUTED_STYLE}">{escape(PRIVILEGE_NOTICE)}</p>'
            f'<p style="margin:20px 0 0;{_BODY_STYLE}">Kind regards,<br>'
            f"{escape(FIRM_NAME)}</p>",
            padding="8px 32px 32px",
        )
    )
    html = _layout(
        title=escape(subject),
        preheader=escape("We have your information and resume. An attorney will be in touch."),
        body=body,
    )
    return RenderedEmail(subject=subject, html=html, text=text)


def lead_page_url(public_web_url: str, lead_id: str) -> str:
    """Absolute URL of the internal lead page: ``PUBLIC_WEB_URL/leads/{id}``."""
    return f"{public_web_url.rstrip('/')}/leads/{lead_id}"


def _format_submitted(submitted_at: datetime) -> str:
    if submitted_at.tzinfo is not None:
        submitted_at = submitted_at.astimezone(UTC)
    return submitted_at.strftime("%d %b %Y, %H:%M UTC")


def _detail_row(label: str, value: str, *, last: bool = False) -> str:
    """One label/value row of the lead summary. ``value`` must already be escaped."""
    border = "" if last else f"border-bottom:1px solid {_BORDER};"
    return (
        "<tr>"
        f'<td width="120" valign="top" style="padding:10px 12px 10px 0;{border}'
        f'{_MUTED_STYLE}font-weight:600;background-color:{_CARD};" bgcolor="{_CARD}">'
        f"{label}</td>"
        f'<td valign="top" style="padding:10px 0;{border}{_BODY_STYLE}font-size:15px;'
        f'line-height:22px;word-break:break-word;background-color:{_CARD};" '
        f'bgcolor="{_CARD}">{value}</td>'
        "</tr>"
    )


def render_attorney_notification(
    *,
    lead_id: str,
    first_name: str,
    last_name: str,
    email: str,
    resume_name: str,
    public_web_url: str,
    submitted_at: datetime | None = None,
) -> RenderedEmail:
    """Notification to the attorney. Links to the lead; never attaches the resume."""
    full_name = f"{first_name} {last_name}".strip()
    url = lead_page_url(public_web_url, lead_id)
    subject = f"New lead: {full_name}"
    submitted = _format_submitted(submitted_at) if submitted_at is not None else None

    text_lines = [
        "A new lead was submitted through the public form.",
        "",
        f"Name:      {full_name}",
        f"Email:     {email}",
        f"Resume:    {resume_name}",
    ]
    if submitted is not None:
        text_lines.append(f"Submitted: {submitted}")
    text_lines += [
        "",
        "Review the lead:",
        url,
        "",
        "The resume is available on the lead page after you sign in.",
        "",
        FIRM_NAME,
    ]
    text = "\n".join(text_lines) + "\n"

    safe_url = escape(url, quote=True)
    rows = [
        _detail_row("Name", escape(full_name)),
        _detail_row("Email", escape(email)),
        _detail_row("Resume", escape(resume_name), last=submitted is None),
    ]
    if submitted is not None:
        rows.append(_detail_row("Submitted", escape(submitted), last=True))

    body = (
        _content_row(
            f'<p style="margin:0 0 12px;{_MUTED_STYLE}text-transform:uppercase;'
            'letter-spacing:0.12em;font-size:12px;font-weight:600;">New lead</p>'
            f'<p style="margin:0 0 20px;{_BODY_STYLE}font-size:22px;line-height:30px;'
            f'font-weight:600;color:{_INK};">{escape(full_name)}</p>'
            '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
            f'border="0" style="background-color:{_CARD};" bgcolor="{_CARD}">'
            + "".join(rows)
            + "</table>",
            padding="32px 32px 0",
        )
        + _content_row(
            '<table role="presentation" cellpadding="0" cellspacing="0" border="0">'
            "<tr>"
            f'<td align="center" style="border-radius:4px;background-color:{_BRASS};" '
            f'bgcolor="{_BRASS}">'
            f'<a href="{safe_url}" style="display:inline-block;padding:12px 28px;'
            f"font-family:{_FONT};font-size:15px;line-height:20px;font-weight:600;"
            f'color:{_BRASS_FG};text-decoration:none;">Review lead</a>'
            "</td>"
            "</tr>"
            "</table>",
            padding="28px 32px 0",
        )
        + _content_row(
            f'<p style="margin:0;{_MUTED_STYLE}">The resume is available on the lead page '
            "after you sign in.</p>",
            padding="20px 32px 32px",
        )
    )
    html = _layout(
        title=escape(subject),
        preheader=escape(f"{full_name} submitted a lead. Review it on the lead page."),
        body=body,
    )
    return RenderedEmail(subject=subject, html=html, text=text)
