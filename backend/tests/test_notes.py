"""Attorney notes: append-only, author snapshotted, returned with the lead detail."""

import uuid

import httpx

from tests.conftest import ATTORNEY_EMAIL
from tests.helpers import create_lead


async def test_create_note_appears_in_detail(auth_client: httpx.AsyncClient) -> None:
    created = (await create_lead(auth_client)).json()
    me = (await auth_client.get("/api/v1/auth/me")).json()

    resp = await auth_client.post(
        f"/api/v1/leads/{created['id']}/notes", json={"body": "  Called, left voicemail.  "}
    )
    assert resp.status_code == 201, resp.text
    note = resp.json()
    assert note["body"] == "Called, left voicemail."  # trimmed
    assert note["author_id"] == me["id"]
    assert note["author_email"] == ATTORNEY_EMAIL
    assert note["created_at"]
    assert set(note) == {"id", "author_id", "author_email", "body", "created_at"}

    detail = (await auth_client.get(f"/api/v1/leads/{created['id']}")).json()
    assert detail["notes"] == [note]
    # the state history is untouched by notes
    assert len(detail["events"]) == 1


async def test_create_note_requires_auth(client: httpx.AsyncClient) -> None:
    created = (await create_lead(client)).json()  # the public form needs no cookie
    resp = await client.post(f"/api/v1/leads/{created['id']}/notes", json={"body": "hi"})
    assert resp.status_code == 401


async def test_create_note_unknown_lead(auth_client: httpx.AsyncClient) -> None:
    resp = await auth_client.post(f"/api/v1/leads/{uuid.uuid4()}/notes", json={"body": "hi"})
    assert resp.status_code == 404


async def test_create_note_rejects_empty_and_whitespace(auth_client: httpx.AsyncClient) -> None:
    created = (await create_lead(auth_client)).json()
    for body in ("", "   ", "\n\t "):
        resp = await auth_client.post(f"/api/v1/leads/{created['id']}/notes", json={"body": body})
        assert resp.status_code == 422, body
        assert resp.json()["detail"][0]["loc"] == ["body", "body"]
    assert (await auth_client.get(f"/api/v1/leads/{created['id']}")).json()["notes"] == []


async def test_create_note_rejects_too_long(auth_client: httpx.AsyncClient) -> None:
    created = (await create_lead(auth_client)).json()
    url = f"/api/v1/leads/{created['id']}/notes"
    assert (await auth_client.post(url, json={"body": "x" * 2001})).status_code == 422
    # exactly the limit is fine, and surrounding whitespace does not count
    assert (await auth_client.post(url, json={"body": " " + "x" * 2000 + " "})).status_code == 201


async def test_notes_are_ordered_oldest_first(auth_client: httpx.AsyncClient) -> None:
    created = (await create_lead(auth_client)).json()
    url = f"/api/v1/leads/{created['id']}/notes"
    for text in ("first", "second", "third"):
        assert (await auth_client.post(url, json={"body": text})).status_code == 201
    notes = (await auth_client.get(f"/api/v1/leads/{created['id']}")).json()["notes"]
    assert [n["body"] for n in notes] == ["first", "second", "third"]
    assert [n["created_at"] for n in notes] == sorted(n["created_at"] for n in notes)
    assert all(n["author_email"] == ATTORNEY_EMAIL for n in notes)


async def test_notes_are_append_only(auth_client: httpx.AsyncClient) -> None:
    created = (await create_lead(auth_client)).json()
    note = (
        await auth_client.post(f"/api/v1/leads/{created['id']}/notes", json={"body": "keep"})
    ).json()
    url = f"/api/v1/leads/{created['id']}/notes/{note['id']}"
    for method in ("PATCH", "PUT", "DELETE"):
        resp = await auth_client.request(method, url, json={"body": "changed"})
        assert resp.status_code in (404, 405), (method, resp.status_code)
