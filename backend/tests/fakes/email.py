from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SentEmail:
    to: str
    subject: str
    html: str
    text: str


class FakeEmailAdapter:
    """Records every ``send`` call. Set ``fail`` to make sends raise."""

    def __init__(self, *, fail: Exception | None = None) -> None:
        self.sent: list[SentEmail] = []
        self.fail = fail

    async def send(self, to: str, subject: str, html: str, text: str) -> None:
        if self.fail is not None:
            raise self.fail
        self.sent.append(SentEmail(to=to, subject=subject, html=html, text=text))

    def sent_to(self, address: str) -> list[SentEmail]:
        return [m for m in self.sent if m.to == address]

    def reset(self) -> None:
        self.sent.clear()
