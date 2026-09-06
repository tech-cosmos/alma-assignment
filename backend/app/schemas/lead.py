import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.lead import LeadState


class LeadCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=200)
    last_name: str = Field(min_length=1, max_length=200)
    email: EmailStr


class LeadRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    first_name: str
    last_name: str
    email: str
    resume_name: str
    resume_type: str
    state: LeadState
    created_at: datetime
    updated_at: datetime
    reached_out_at: datetime | None
    reached_out_by: uuid.UUID | None
    reached_out_by_email: str | None = None


class LeadEventRead(BaseModel):
    """One entry in a lead's history. ``actor_*`` are null for the prospect's submission."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    from_state: LeadState | None
    to_state: LeadState
    actor_id: uuid.UUID | None
    actor_email: str | None
    created_at: datetime


NOTE_MAX_CHARS = 2000


class LeadNoteCreate(BaseModel):
    """Body of ``POST /leads/{id}/notes``. Whitespace is trimmed before the length check."""

    body: str = Field(min_length=1, max_length=NOTE_MAX_CHARS)

    @field_validator("body", mode="before")
    @classmethod
    def _strip(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class LeadNoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    author_id: uuid.UUID | None
    author_email: str
    body: str
    created_at: datetime


class LeadDetail(LeadRead):
    events: list[LeadEventRead]
    # Attorney notes, oldest first. Append-only: there is no update or delete.
    notes: list[LeadNoteRead]


class LeadCounts(BaseModel):
    pending: int
    reached_out: int


class LeadList(BaseModel):
    items: list[LeadRead]
    total: int
    limit: int
    offset: int
    # Counts across all leads, independent of the ``state`` filter (for the filter tabs).
    counts: LeadCounts


class LeadStateUpdate(BaseModel):
    state: LeadState
