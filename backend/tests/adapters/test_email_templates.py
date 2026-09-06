from app.adapters.email.templates import (
    lead_page_url,
    render_attorney_notification,
    render_prospect_confirmation,
)


def test_prospect_confirmation_addresses_prospect_by_name() -> None:
    email = render_prospect_confirmation(first_name="Ada", last_name="Lovelace")
    assert email.subject
    assert "Hi Ada Lovelace" in email.text
    assert "Hi Ada Lovelace" in email.html
    assert "resume" in email.text.lower()


def test_prospect_confirmation_escapes_html_in_names() -> None:
    email = render_prospect_confirmation(first_name="<script>", last_name="x")
    assert "<script>" not in email.html
    assert "&lt;script&gt;" in email.html
    assert "<script>" in email.text  # plain text is not escaped


def test_lead_page_url_strips_trailing_slash() -> None:
    assert (
        lead_page_url("http://localhost:3000/", "abc")
        == "http://localhost:3000/leads/abc"
    )
    assert (
        lead_page_url("https://alma.example", "abc") == "https://alma.example/leads/abc"
    )


def test_attorney_notification_links_to_lead_and_lists_fields() -> None:
    email = render_attorney_notification(
        lead_id="1d3a0b9e-0000-4000-8000-000000000001",
        first_name="Ada",
        last_name="Lovelace",
        email="ada@example.com",
        resume_name="ada-cv.pdf",
        public_web_url="http://localhost:3000",
    )
    url = "http://localhost:3000/leads/1d3a0b9e-0000-4000-8000-000000000001"
    assert "Ada Lovelace" in email.subject
    for body in (email.text, email.html):
        assert url in body
        assert "ada@example.com" in body
        assert "ada-cv.pdf" in body
    assert f'href="{url}"' in email.html


def test_attorney_notification_escapes_user_input_in_html() -> None:
    email = render_attorney_notification(
        lead_id="x",
        first_name="<b>",
        last_name="&",
        email="a@b.c",
        resume_name="<img src=x>.pdf",
        public_web_url="http://localhost:3000",
    )
    assert "<b>" not in email.html
    assert "<img" not in email.html
    assert "&lt;b&gt; &amp;" in email.html
