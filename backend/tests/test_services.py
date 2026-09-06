"""Service-level tests that bypass HTTP."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import Lead, LeadState
from app.models.user import User
from app.repositories.lead import LeadRepository
from app.services.lead import InvalidTransition, LeadService
from app.services.resume import InvalidResume, validate_resume
from tests.fakes import FakeStorageAdapter
from tests.helpers import PDF_BYTES


def _lead(state: LeadState = LeadState.PENDING) -> Lead:
    return Lead(
        id=uuid.uuid4(),
        first_name="A",
        last_name="B",
        email="a@example.com",
        resume_key="resumes/x/y.pdf",
        resume_name="y.pdf",
        resume_type="application/pdf",
        state=state,
    )


async def test_mark_reached_out_transition(db_session: AsyncSession, attorney: User) -> None:
    repo = LeadRepository(db_session)
    lead = await repo.add(_lead())
    service = LeadService(repo, FakeStorageAdapter())

    updated = await service.mark_reached_out(lead, attorney)
    assert updated.state is LeadState.REACHED_OUT
    assert updated.reached_out_at is not None
    assert updated.reached_out_by == attorney.id

    with pytest.raises(InvalidTransition):
        await service.mark_reached_out(lead, attorney)
    with pytest.raises(InvalidTransition):
        await service.transition(lead, LeadState.PENDING, attorney)


async def test_create_lead_cleans_up_storage_on_db_failure(db_session: AsyncSession) -> None:
    from app.schemas.lead import LeadCreate

    storage = FakeStorageAdapter()

    class BrokenRepo(LeadRepository):
        async def add(self, lead: Lead) -> Lead:
            raise RuntimeError("db down")

    service = LeadService(BrokenRepo(db_session), storage)
    upload = validate_resume("cv.pdf", PDF_BYTES, max_bytes=1024)
    with pytest.raises(RuntimeError):
        await service.create(
            LeadCreate(first_name="A", last_name="B", email="a@example.com"), upload
        )
    assert storage.objects == {}


def test_validate_resume_uses_magic_bytes() -> None:
    upload = validate_resume("anything.txt", PDF_BYTES, max_bytes=1024)
    assert upload.content_type == "application/pdf" and upload.extension == "pdf"
    assert validate_resume(None, PDF_BYTES, max_bytes=1024).filename == "resume.pdf"
    with pytest.raises(InvalidResume):
        validate_resume("cv.pdf", b"nope", max_bytes=1024)
    with pytest.raises(InvalidResume):
        validate_resume("cv.pdf", PDF_BYTES, max_bytes=4)
