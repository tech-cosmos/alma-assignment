import logging

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text

from app.api.deps import SessionDep

log = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


@router.get("/health")
async def health(session: SessionDep) -> dict[str, str]:
    try:
        await session.execute(text("SELECT 1"))
    except Exception as exc:
        log.exception("Health check failed")
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, detail="database unavailable"
        ) from exc
    return {"status": "ok", "db": "ok"}
