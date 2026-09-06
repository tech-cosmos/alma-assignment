import re
from datetime import UTC, datetime

import pytest

from app.adapters.email.templates import (
    PRIVILEGE_NOTICE,
    lead_page_url,
    render_attorney_notification,
    render_prospect_confirmation,
)

LEAD_ID = "1d3a0b9e-0000-4000-8000-000000000001"
WEB = "http://localhost:3000"
LEAD_URL = f"{WEB}/leads/{LEAD_ID}"

_URL_RE = re.compile(r"https?://[^\s\"'<>]+")


def _attorney(**overrides: object):  # type: ignore[no-untyped-def]
    kwargs: dict[str, object] = dict(
        lead_id=LEAD_ID,
        first_name="Ada",
        last_name="Lovelace",
        email="ada@example.com",
        resume_name="ada-cv.pdf",
        public_web_url=WEB,
    )
    kwargs.update(overrides)
    return render_attorney_notification(**kwargs)  # type: ignore[arg-type]


def _assert_email_safe_html(html: str, *, allowed_urls: set[str]) -> None:
    lowered = html.lower()
    assert "<script" not in lowered
    assert "<img" not in lowered
    assert "javascript:" not in lowered
    assert "@import" not in lowered and "@font-face" not in lowered
    assert set(_URL_RE.findall(html)) == allowed_urls


# --- prospect confirmation ---------------------------------------------------


def test_prospect_confirmation_addresses_prospect_by_name() -> None:
    email = render_prospect_confirmation(first_name="Ada", last_name="Lovelace")
    assert email.subject
    assert "Hi Ada Lovelace" in email.text
    assert "Hi Ada Lovelace" in email.html
    assert "resume" in email.text.lower()


def test_prospect_confirmation_explains_next_steps_and_privilege() -> None:
    email = render_prospect_confirmation(first_name="Ada", last_name="Lovelace")
    for body in (email.text, email.html):
        assert "review your background" in body
        assert "attorney reaches out" in body
        assert "do nothing for now" in body
        assert PRIVILEGE_NOTICE in body
        assert "Alma Immigration" in body


def test_prospect_confirmation_escapes_html_in_names() -> None:
    email = render_prospect_confirmation(first_name="<script>", last_name="x")
    assert "<script>" not in email.html
    assert "&lt;script&gt;" in email.html
    assert "<script>" in email.text  # plain text is not escaped


def test_prospect_confirmation_html_is_email_safe() -> None:
    email = render_prospect_confirmation(first_name="Ada", last_name="Lovelace")
    _assert_email_safe_html(email.html, allowed_urls=set())


# --- attorney notification ---------------------------------------------------


def test_lead_page_url_strips_trailing_slash() -> None:
    assert lead_page_url("http://localhost:3000/", "abc") == "http://localhost:3000/leads/abc"
    assert lead_page_url("https://alma.example", "abc") == "https://alma.example/leads/abc"


def test_attorney_notification_links_to_lead_and_lists_fields() -> None:
    email = _attorney()
    assert "Ada Lovelace" in email.subject
    for body in (email.text, email.html):
        assert LEAD_URL in body
        assert "ada@example.com" in body
        assert "ada-cv.pdf" in body
        assert "sign in" in body
    assert f'href="{LEAD_URL}"' in email.html
    assert "Review lead" in email.html


def test_attorney_notification_escapes_user_input_in_html() -> None:
    email = _attorney(first_name="<b>", last_name="&", email="a@b.c", resume_name="<img src=x>.pdf")
    assert "<b>" not in email.html
    assert "<img" not in email.html
    assert "&lt;b&gt; &amp;" in email.html


def test_attorney_notification_escapes_script_in_name() -> None:
    email = _attorney(first_name="<script>alert(1)</script>", last_name="x")
    assert "<script" not in email.html.lower()
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in email.html
    assert "<script>" in email.text


def test_attorney_notification_html_is_email_safe_and_only_links_to_lead() -> None:
    email = _attorney()
    _assert_email_safe_html(email.html, allowed_urls={LEAD_URL})
    # Exactly one anchor, and it is the lead page.
    assert email.html.count("<a ") == 1


def test_attorney_notification_does_not_link_the_resume_file() -> None:
    email = _attorney(resume_name="ada-cv.pdf")
    assert "resume" not in _URL_RE.findall(email.html)[0]
    assert f"{LEAD_URL}/resume" not in email.html
    assert f"{LEAD_URL}/resume" not in email.text


@pytest.mark.parametrize(
    ("submitted_at", "expected"),
    [
        (datetime(2026, 9, 6, 14, 5, tzinfo=UTC), "06 Sep 2026, 14:05 UTC"),
        (datetime(2026, 9, 6, 14, 5), "06 Sep 2026, 14:05 UTC"),  # naive treated as UTC
    ],
)
def test_attorney_notification_shows_submitted_time_when_given(
    submitted_at: datetime, expected: str
) -> None:
    email = _attorney(submitted_at=submitted_at)
    assert expected in email.html
    assert expected in email.text


def test_attorney_notification_omits_submitted_row_without_time() -> None:
    email = _attorney()
    assert "Submitted" not in email.html
    assert "Submitted:" not in email.text
