import uuid

import httpx
import pytest

from app.models.lead import LeadState
from tests.conftest import ATTORNEY_EMAIL
from tests.fakes import FakeEmailAdapter, FakeStorageAdapter
from tests.helpers import DOC_BYTES, PDF_BYTES, create_lead, docx_bytes, plain_zip_bytes


async def test_create_lead_persists_uploads_and_emails(
    client: httpx.AsyncClient, email_adapter: FakeEmailAdapter, storage_adapter: FakeStorageAdapter
) -> None:
    resp = await create_lead(client)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["first_name"] == "Ada"
    assert body["last_name"] == "Lovelace"
    assert body["email"] == "ada@example.com"
    assert body["state"] == "PENDING"
    assert body["resume_name"] == "resume.pdf"
    assert body["resume_type"] == "application/pdf"
    assert body["reached_out_at"] is None
    assert body["reached_out_by"] is None
    assert "resume_key" not in body

    # resume stored under an opaque key
    assert len(storage_adapter.objects) == 1
    key, (data, content_type) = next(iter(storage_adapter.objects.items()))
    assert key.startswith(f"resumes/{body['id']}/") and key.endswith(".pdf")
    assert data == PDF_BYTES and content_type == "application/pdf"

    # both emails were dispatched after commit
    recipients = {m.to for m in email_adapter.sent}
    assert recipients == {"ada@example.com", ATTORNEY_EMAIL}
    attorney_mail = next(m for m in email_adapter.sent if m.to == ATTORNEY_EMAIL)
    assert f"http://web.test/leads/{body['id']}" in attorney_mail.text
    assert "Ada Lovelace" in attorney_mail.subject
    prospect_mail = next(m for m in email_adapter.sent if m.to == "ada@example.com")
    assert "Ada" in prospect_mail.text


async def test_create_lead_survives_email_failure(
    client: httpx.AsyncClient, email_adapter: FakeEmailAdapter, auth_client: httpx.AsyncClient
) -> None:
    email_adapter.fail = True
    resp = await create_lead(client)
    assert resp.status_code == 201
    assert email_adapter.sent == []
    listing = await auth_client.get("/api/v1/leads")
    assert listing.json()["total"] == 1


@pytest.mark.parametrize(
    ("filename", "content", "expected_type"),
    [
        ("cv.pdf", PDF_BYTES, "application/pdf"),
        ("cv.doc", DOC_BYTES, "application/msword"),
        (
            "cv.docx",
            docx_bytes(),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ),
    ],
)
async def test_create_lead_accepts_supported_types(
    client: httpx.AsyncClient, filename: str, content: bytes, expected_type: str
) -> None:
    resp = await create_lead(client, filename=filename, content=content, content_type="text/plain")
    assert resp.status_code == 201, resp.text
    assert resp.json()["resume_type"] == expected_type


@pytest.mark.parametrize(
    ("filename", "content"),
    [
        ("resume.pdf", b"this is not a pdf at all"),  # extension lies
        ("resume.docx", plain_zip_bytes()),  # zip but not OOXML
        ("resume.exe", b"MZ\x90\x00"),
        ("resume.pdf", b""),
    ],
)
async def test_create_lead_rejects_bad_files(
    client: httpx.AsyncClient, filename: str, content: bytes, storage_adapter: FakeStorageAdapter
) -> None:
    resp = await create_lead(client, filename=filename, content=content)
    assert resp.status_code == 422, resp.text
    assert storage_adapter.objects == {}


async def test_create_lead_rejects_oversized_resume(
    client: httpx.AsyncClient, storage_adapter: FakeStorageAdapter
) -> None:
    big = PDF_BYTES + b"0" * (5 * 1024 * 1024)
    resp = await create_lead(client, content=big)
    assert resp.status_code == 422
    assert "5 MB" in resp.json()["detail"]
    assert storage_adapter.objects == {}


async def test_create_lead_validates_fields(client: httpx.AsyncClient) -> None:
    resp = await create_lead(client, email="not-an-email")
    assert resp.status_code == 422
    resp = await client.post("/api/v1/leads", data={"first_name": "A"})
    assert resp.status_code == 422
    resp = await create_lead(client, first_name="   ")
    assert resp.status_code == 422


async def test_list_requires_auth(client: httpx.AsyncClient) -> None:
    assert (await client.get("/api/v1/leads")).status_code == 401
    assert (await client.get(f"/api/v1/leads/{uuid.uuid4()}")).status_code == 401
    assert (
        await client.patch(f"/api/v1/leads/{uuid.uuid4()}/state", json={"state": "REACHED_OUT"})
    ).status_code == 401
    assert (await client.get(f"/api/v1/leads/{uuid.uuid4()}/resume")).status_code == 401


async def test_list_rejects_bad_token(client: httpx.AsyncClient) -> None:
    client.cookies.set("access_token", "garbage")
    assert (await client.get("/api/v1/leads")).status_code == 401


async def test_list_with_auth_returns_leads(auth_client: httpx.AsyncClient) -> None:
    await create_lead(auth_client, email="one@example.com")
    await create_lead(auth_client, email="two@example.com", first_name="Bob")
    resp = await auth_client.get("/api/v1/leads")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert body["limit"] == 50 and body["offset"] == 0
    assert {item["email"] for item in body["items"]} == {"one@example.com", "two@example.com"}
    assert all(
        set(item) >= {"first_name", "last_name", "email", "resume_name"} for item in body["items"]
    )

    resp = await auth_client.get("/api/v1/leads", params={"limit": 1, "offset": 1})
    assert resp.json()["total"] == 2 and len(resp.json()["items"]) == 1


async def test_list_filters_by_state(auth_client: httpx.AsyncClient) -> None:
    created = (await create_lead(auth_client)).json()
    await create_lead(auth_client, email="other@example.com")
    await auth_client.patch(f"/api/v1/leads/{created['id']}/state", json={"state": "REACHED_OUT"})

    pending = (await auth_client.get("/api/v1/leads", params={"state": "PENDING"})).json()
    reached = (await auth_client.get("/api/v1/leads", params={"state": "REACHED_OUT"})).json()
    assert pending["total"] == 1 and pending["items"][0]["email"] == "other@example.com"
    assert reached["total"] == 1 and reached["items"][0]["id"] == created["id"]
    assert (await auth_client.get("/api/v1/leads", params={"state": "BOGUS"})).status_code == 422


async def test_get_lead(auth_client: httpx.AsyncClient) -> None:
    created = (await create_lead(auth_client)).json()
    resp = await auth_client.get(f"/api/v1/leads/{created['id']}")
    assert resp.status_code == 200 and resp.json()["id"] == created["id"]
    assert (await auth_client.get(f"/api/v1/leads/{uuid.uuid4()}")).status_code == 404


async def test_valid_transition_sets_reached_out_fields(auth_client: httpx.AsyncClient) -> None:
    created = (await create_lead(auth_client)).json()
    me = (await auth_client.get("/api/v1/auth/me")).json()

    resp = await auth_client.patch(
        f"/api/v1/leads/{created['id']}/state", json={"state": "REACHED_OUT"}
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["state"] == LeadState.REACHED_OUT.value
    assert body["reached_out_at"] is not None
    assert body["reached_out_by"] == me["id"]

    again = await auth_client.get(f"/api/v1/leads/{created['id']}")
    assert again.json()["state"] == "REACHED_OUT"
    assert again.json()["reached_out_at"] == body["reached_out_at"]


async def test_invalid_transitions_return_409(auth_client: httpx.AsyncClient) -> None:
    created = (
        await auth_client.post(
            "/api/v1/leads",
            data={"first_name": "Ada", "last_name": "L", "email": "a@example.com"},
            files={"resume": ("r.pdf", PDF_BYTES, "application/pdf")},
        )
    ).json()
    url = f"/api/v1/leads/{created['id']}/state"

    # PENDING -> PENDING is not a transition
    assert (await auth_client.patch(url, json={"state": "PENDING"})).status_code == 409

    assert (await auth_client.patch(url, json={"state": "REACHED_OUT"})).status_code == 200
    # REACHED_OUT -> REACHED_OUT and REACHED_OUT -> PENDING are both invalid
    resp = await auth_client.patch(url, json={"state": "REACHED_OUT"})
    assert resp.status_code == 409
    assert "REACHED_OUT" in resp.json()["detail"]
    assert (await auth_client.patch(url, json={"state": "PENDING"})).status_code == 409

    # unknown states are a validation error, missing leads are 404
    assert (await auth_client.patch(url, json={"state": "CLOSED"})).status_code == 422
    assert (
        await auth_client.patch(
            f"/api/v1/leads/{uuid.uuid4()}/state", json={"state": "REACHED_OUT"}
        )
    ).status_code == 404


async def test_resume_streams_from_local_storage(auth_client: httpx.AsyncClient) -> None:
    created = (await create_lead(auth_client)).json()
    resp = await auth_client.get(f"/api/v1/leads/{created['id']}/resume")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert 'filename="resume.pdf"' in resp.headers["content-disposition"]
    assert resp.content == PDF_BYTES


async def test_resume_redirects_when_presigned(
    auth_client: httpx.AsyncClient, storage_adapter: FakeStorageAdapter
) -> None:
    created = (await create_lead(auth_client)).json()
    storage_adapter.presign = True
    resp = await auth_client.get(f"/api/v1/leads/{created['id']}/resume", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["location"].startswith("https://signed.example/resumes/")
