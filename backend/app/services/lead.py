"""Lead business logic, including the single allowed state transition.

Every state change (including the initial submission) is appended to ``lead_events``
in the same transaction, so the history can never drift from the lead row.
"""

import logging
import secrets
import uuid
from datetime import UTC, datetime

from app.adapters.storage.base import StorageAdapter
from app.models.lead import Lead, LeadState
from app.models.lead_event import LeadEvent
from app.models.lead_note import LeadNote
from app.models.user import User
from app.repositories.lead import LeadRepository
from app.schemas.lead import LeadCreate
from app.services.resume import ResumeUpload

log = logging.getLogger(__name__)


class InvalidTransition(Exception):
    """Raised for any state change other than PENDING -> REACHED_OUT."""

    def __init__(self, current: LeadState, target: LeadState) -> None:
        self.current = current
        self.target = target
        super().__init__(f"Cannot move lead from {current.value} to {target.value}.")


class LeadService:
    def __init__(self, repo: LeadRepository, storage: StorageAdapter) -> None:
        self._repo = repo
        self._storage = storage

    async def create(self, data: LeadCreate, resume: ResumeUpload) -> Lead:
        lead_id = uuid.uuid4()
        key = f"resumes/{lead_id}/{secrets.token_urlsafe(16)}.{resume.extension}"
        await self._storage.put(key, resume.data, resume.content_type)
        lead = Lead(
            id=lead_id,
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            resume_key=key,
            resume_name=resume.filename,
            resume_type=resume.content_type,
            state=LeadState.PENDING,
        )
        try:
            await self._repo.add(lead)
            # Submission has no actor: the prospect is not a user.
            await self._repo.add_event(
                LeadEvent(lead_id=lead_id, from_state=None, to_state=LeadState.PENDING)
            )
            await self._repo.commit()
            await self._repo.refresh(lead)
        except Exception:
            log.warning("Lead insert failed; removing uploaded resume %s", key)
            await self._storage.delete(key)
            raise
        return lead

    async def mark_reached_out(self, lead: Lead, user: User) -> Lead:
        if lead.state is not LeadState.PENDING:
            raise InvalidTransition(lead.state, LeadState.REACHED_OUT)
        now = datetime.now(UTC)
        lead.state = LeadState.REACHED_OUT
        lead.reached_out_at = now
        lead.reached_out_by = user.id
        await self._repo.add_event(
            LeadEvent(
                lead_id=lead.id,
                from_state=LeadState.PENDING,
                to_state=LeadState.REACHED_OUT,
                actor_id=user.id,
                actor_email=user.email,
                created_at=now,
            )
        )
        await self._repo.commit()
        return await self._repo.refresh(lead)

    async def add_note(self, lead: Lead, user: User, body: str) -> LeadNote:
        """Append a plain-text note by ``user``; the author's email is snapshotted on the row."""
        note = LeadNote(lead_id=lead.id, author_id=user.id, author_email=user.email, body=body)
        await self._repo.add_note(note)
        await self._repo.commit()
        await self._repo.refresh_note(note)
        return note

    async def transition(self, lead: Lead, target: LeadState, user: User) -> Lead:
        """Apply a requested state; only PENDING -> REACHED_OUT is defined."""
        if target is LeadState.REACHED_OUT:
            return await self.mark_reached_out(lead, user)
        raise InvalidTransition(lead.state, target)
