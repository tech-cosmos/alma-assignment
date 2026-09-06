import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.user import User


class LeadState(enum.StrEnum):
    PENDING = "PENDING"
    REACHED_OUT = "REACHED_OUT"


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    resume_key: Mapped[str] = mapped_column(String, nullable=False)
    resume_name: Mapped[str] = mapped_column(String, nullable=False)
    resume_type: Mapped[str] = mapped_column(String, nullable=False)
    state: Mapped[LeadState] = mapped_column(
        Enum(LeadState, name="lead_state", native_enum=True),
        nullable=False,
        default=LeadState.PENDING,
        server_default=LeadState.PENDING.value,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    reached_out_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reached_out_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    # Eagerly joined so every read (list, get, refresh) can report who reached out.
    reached_out_by_user: Mapped[User | None] = relationship(User, lazy="joined")

    @property
    def reached_out_by_email(self) -> str | None:
        return self.reached_out_by_user.email if self.reached_out_by_user else None
