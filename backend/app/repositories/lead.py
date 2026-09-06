import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import Lead, LeadState


class LeadRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, lead: Lead) -> Lead:
        self._session.add(lead)
        await self._session.flush()
        return lead

    async def get(self, lead_id: uuid.UUID) -> Lead | None:
        return await self._session.get(Lead, lead_id)

    async def list(
        self, *, state: LeadState | None, limit: int, offset: int
    ) -> tuple[Sequence[Lead], int]:
        base = select(Lead)
        count = select(func.count()).select_from(Lead)
        if state is not None:
            base = base.where(Lead.state == state)
            count = count.where(Lead.state == state)
        stmt = base.order_by(Lead.created_at.desc(), Lead.id).limit(limit).offset(offset)
        items = (await self._session.execute(stmt)).scalars().all()
        total = (await self._session.execute(count)).scalar_one()
        return items, total

    async def commit(self) -> None:
        await self._session.commit()

    async def refresh(self, lead: Lead) -> Lead:
        """Reload server-generated columns (timestamps) after a commit."""
        await self._session.refresh(lead)
        return lead
