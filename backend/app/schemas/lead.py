import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

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


class LeadList(BaseModel):
    items: list[LeadRead]
    total: int
    limit: int
    offset: int


class LeadStateUpdate(BaseModel):
    state: LeadState
