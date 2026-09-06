"""Append-only history of lead state changes: who moved what, and when."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.lead import LeadState


class LeadEvent(Base):
    __tablename__ = "lead_events"
    __table_args__ = (Index("ix_lead_events_lead_id_created_at", "lead_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False
    )
    # None for the submission event (there is no prior state).
    from_state: Mapped[LeadState | None] = mapped_column(
        Enum(LeadState, name="lead_state", native_enum=True), nullable=True
    )
    to_state: Mapped[LeadState] = mapped_column(
        Enum(LeadState, name="lead_state", native_enum=True), nullable=False
    )
    # None when the prospect submitted the form (no signed-in actor).
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    # Snapshot of the actor's email so history stays readable if the user is later removed.
    actor_email: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
