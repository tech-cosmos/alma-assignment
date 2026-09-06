from app.adapters.email.base import EmailMessage


class FakeEmailAdapter:
    """Records every ``send`` call. Set ``fail`` to make sends raise."""

    def __init__(self, *, fail: bool = False) -> None:
        self.sent: list[EmailMessage] = []
        self.fail = fail

    async def send(self, message: EmailMessage) -> None:
        if self.fail:
            raise RuntimeError("smtp down")
        self.sent.append(message)

    def sent_to(self, address: str) -> list[EmailMessage]:
        return [m for m in self.sent if m.to == address]

    def reset(self) -> None:
        self.sent.clear()
