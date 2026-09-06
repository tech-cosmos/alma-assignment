# Adapters (Track B)

Email and storage side-effects behind two small Protocols. Everything here is
self-contained: no imports from `app.core`, `app.services`, or the models.

## Contracts (`base.py`)

```python
class EmailAdapter(Protocol):
    async def send(self, to: str, subject: str, html: str, text: str) -> None: ...

class StorageAdapter(Protocol):
    async def put(self, key: str, data: bytes, content_type: str) -> None: ...
    async def get_url(self, key: str, expires_in: int = 900) -> str: ...
    async def open(self, key: str) -> bytes: ...   # raises FileNotFoundError
```

## Wiring from settings

```python
from app.adapters.email import build_email_adapter
from app.adapters.storage import build_storage_adapter

email = build_email_adapter(
    settings.email_provider,             # console | smtp | ses
    email_from=settings.email_from,
    smtp_host=settings.smtp_host,
    smtp_port=settings.smtp_port,
    aws_region=settings.aws_region,
)
storage = build_storage_adapter(
    settings.storage_provider,           # local | s3
    local_dir=settings.storage_local_dir,
    s3_bucket=settings.s3_bucket,
    s3_endpoint_url=settings.s3_endpoint_url or None,  # blank -> AWS
    aws_region=settings.aws_region,
)
```

Build once at startup and inject through `app.api.deps`; the boto3 clients are
created in the constructor. In tests, override the dependencies with
`tests.fakes.FakeEmailAdapter` / `FakeStorageAdapter`.

## Sending the two emails

```python
from app.adapters.email import render_attorney_notification, render_prospect_confirmation

msg = render_prospect_confirmation(first_name=lead.first_name, last_name=lead.last_name)
background.add_task(email.send, lead.email, msg.subject, msg.html, msg.text)

msg = render_attorney_notification(
    lead_id=str(lead.id),
    first_name=lead.first_name,
    last_name=lead.last_name,
    email=lead.email,
    resume_name=lead.resume_name,
    public_web_url=settings.public_web_url,
)
background.add_task(email.send, settings.attorney_email, msg.subject, msg.html, msg.text)
```

Adapters raise on failure; the background task wrapper should catch and log
(PLAN section 5: email failure never fails the request).

## Resume route (`GET /api/v1/leads/{id}/resume`)

- `S3StorageAdapter.get_url` returns a presigned URL: respond `302`.
- `LocalStorageAdapter.get_url` returns `{url_prefix}/{key}` (default prefix
  `/api/v1/storage`); there is no route behind it. For `local`, stream
  `await storage.open(lead.resume_key)` with `lead.resume_type` as the media
  type instead of redirecting. `isinstance(storage, LocalStorageAdapter)` or a
  `settings.storage_provider` check is fine.
- Keys are caller-chosen; use something like `resumes/{lead_id}{suffix}`.
  `LocalStorageAdapter` rejects keys that escape the base directory.

## Dependencies to add to `pyproject.toml`

Runtime: `aiosmtplib`, `boto3`.
Dev: `moto[s3,ses]`, `aiosmtpd`, `pytest-asyncio`, `boto3-stubs[s3,ses]` (optional, for mypy).

Tests use explicit `@pytest.mark.asyncio` marks, so they work in both
`asyncio_mode = "strict"` and `"auto"`. `tests/__init__.py` and
`tests/adapters/__init__.py` exist so pytest puts `backend/` on `sys.path`.

## Provider notes

- `smtp`: no auth, no TLS. Meant for Mailpit (`SMTP_HOST=mailpit`, `SMTP_PORT=1025`).
- `ses`: `EMAIL_FROM` must be a verified SES identity; credentials via the AWS chain.
- `s3`: one code path for AWS S3, Cloudflare R2, MinIO. Setting `S3_ENDPOINT_URL`
  switches to SigV4 + path-style addressing. R2 wants `AWS_REGION=auto`.
