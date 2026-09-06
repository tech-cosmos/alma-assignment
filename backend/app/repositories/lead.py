import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import Lead, LeadState
from app.models.lead_event import LeadEvent


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

    async def count_by_state(self) -> dict[LeadState, int]:
        """Number of leads in every state (states with no leads map to 0)."""
        stmt = select(Lead.state, func.count()).group_by(Lead.state)
        rows = (await self._session.execute(stmt)).all()
        counts = dict.fromkeys(LeadState, 0)
        for state, n in rows:
            counts[LeadState(state)] = n
        return counts

    async def add_event(self, event: LeadEvent) -> LeadEvent:
        self._session.add(event)
        await self._session.flush()
        return event

    async def list_events(self, lead_id: uuid.UUID) -> Sequence[LeadEvent]:
        """History for one lead, oldest first."""
        stmt = (
            select(LeadEvent)
            .where(LeadEvent.lead_id == lead_id)
            .order_by(LeadEvent.created_at, LeadEvent.id)
        )
        return (await self._session.execute(stmt)).scalars().all()

    async def commit(self) -> None:
        await self._session.commit()

    async def refresh(self, lead: Lead) -> Lead:
        """Reload server-generated columns (timestamps) after a commit."""
        await self._session.refresh(lead)
        return lead
