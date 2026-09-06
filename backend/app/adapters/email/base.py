"""Email adapter protocol.

Track A (backend core) owns this file. Track B owns the concrete implementations
(``console.py``, ``smtp.py``, ``ses.py``). Each implementation module must expose::

    def create_adapter(settings: Settings) -> EmailAdapter: ...

``app.api.deps.get_email_adapter`` imports the module named by ``EMAIL_PROVIDER`` and
calls that factory. Implementations must raise on failure; the caller logs and swallows.
"""

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class EmailMessage:
    to: str
    subject: str
    text: str
    html: str | None = None


@runtime_checkable
class EmailAdapter(Protocol):
    async def send(self, message: EmailMessage) -> None:
        """Deliver one message. Raise on failure."""
        ...
