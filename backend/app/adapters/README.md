# Adapters

Email and storage side-effects behind two small Protocols (`base.py` in each
sub-package). Provider modules are selected by environment and loaded by
`app.api.deps._load_adapter`, which imports `app.adapters.<kind>.<provider>`
and calls its `create_adapter(settings)`.

## Contracts

```python
@dataclass(frozen=True)
class EmailMessage:
    to: str
    subject: str
    text: str
    html: str | None = None


class EmailAdapter(Protocol):
    async def send(self, message: EmailMessage) -> None: ...  # raises on failure


class StorageAdapter(Protocol):
    async def put(self, key: str, data: bytes, content_type: str) -> None: ...
    async def delete(self, key: str) -> None: ...  # never raises on missing key
    async def stream(self, key: str) -> AsyncIterator[bytes]: ...  # raises KeyError if missing
    async def presigned_url(
        self, key: str, *, expires_in: int
    ) -> str | None: ...  # None -> API streams
```

## Providers

| Kind | `*_PROVIDER` | Module | Notes |
|---|---|---|---|
| email | `console` | `email/console.py` | Prints the text body to stdout |
| email | `smtp` | `email/smtp.py` | aiosmtplib, no auth/TLS, for Mailpit |
| email | `ses` | `email/ses.py` | boto3 `send_email` in a worker thread; `EMAIL_FROM` must be a verified identity |
| storage | `local` | `storage/local.py` | Atomic writes under `STORAGE_LOCAL_DIR`; rejects path-escaping keys |
| storage | `s3` | `storage/s3.py` | AWS S3, Cloudflare R2, MinIO via `S3_ENDPOINT_URL`; presigned GET URLs |

Templates for the two lead emails live in `email/templates.py`; all user input
is HTML-escaped and the attorney email links to the lead page rather than
attaching the resume. `app.services.notify.LeadNotifier` renders and sends them.

Test doubles are in `tests/fakes/` and are injected through FastAPI dependency
overrides in `tests/conftest.py`.
