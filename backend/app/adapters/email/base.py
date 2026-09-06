"""Email adapter contract.

Implementations must be safe to call from FastAPI ``BackgroundTasks``: they
raise on failure and never swallow errors, so the caller decides whether to
log or retry. Callers never let an email failure fail the HTTP request.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class EmailAdapter(Protocol):
    """Send a single multipart (text + html) message."""

    async def send(self, to: str, subject: str, html: str, text: str) -> None: ...
