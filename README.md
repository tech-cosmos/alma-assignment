# Alma Lead Intake

Lead intake for an immigration law firm: a public form where prospects submit their name, email and resume, two emails on every submission (confirmation to the prospect, notification to an attorney), and an authenticated internal UI where attorneys review leads and mark them as reached out.

- API: FastAPI (Python 3.12), SQLAlchemy 2.0 async, Alembic, Postgres 16
- Web: Next.js 15 App Router, TypeScript, Tailwind, shadcn/ui
- Email and storage are pluggable adapters. Local defaults need no cloud account.

Design rationale lives in [docs/DESIGN.md](docs/DESIGN.md). Coding-agent usage is in [docs/AGENTS.md](docs/AGENTS.md) and attribution in [NOTES.md](NOTES.md).

## Run locally

Prerequisite: Docker Desktop (or Docker Engine with the Compose plugin).

```bash
docker compose up
```

That is the whole setup. Compose starts four services and the API container applies migrations and seeds the attorney login before serving. `make up` does the same in the background and prints the URLs.

| What | URL |
|---|---|
| Public lead form | http://localhost:3000 |
| Internal UI (attorney login required) | http://localhost:3000/leads |
| Mailpit inbox (every email the app sends) | http://localhost:8025 |
| API docs (OpenAPI) | http://localhost:8000/docs |
| Health check | http://localhost:8000/api/v1/health |

Default login for the internal UI:

```
email:    attorney@example.com
password: password123
```

Both values come from `SEED_USER_EMAIL` and `SEED_USER_PASSWORD` in `.env.example` and can be changed before first start.

### End-to-end walkthrough

1. Open http://localhost:3000 and submit the form with a PDF, DOC or DOCX resume (max 5 MB).
2. Open http://localhost:8025. Two messages arrive: a confirmation addressed to the prospect and a notification addressed to `ATTORNEY_EMAIL` with a link to the lead.
3. Open http://localhost:3000/leads, log in, click the lead to open it (the PDF renders on the page), and click **Mark reached out**. The state changes from `PENDING` to `REACHED_OUT`, and the lead's history records who did it and when.
4. On the same page, type into the note box under **History** and click **Add note**. The note appears in the timeline with your email and stays after a reload; notes cannot be edited or deleted.

### Useful commands

```bash
make up        # build and start everything detached
make logs      # tail all service logs
make down      # stop (keeps database and resumes)
make clean     # stop and delete volumes
make migrate   # re-run alembic upgrade head in the api container
make seed      # re-create the attorney user in the api container
```

## Configuration

All settings are environment variables, documented one per line in [.env.example](.env.example). Compose uses those same defaults when no `.env` file exists, so copying the file is optional:

```bash
cp .env.example .env   # then edit, then docker compose up
```

### Switching email to Amazon SES

The default `EMAIL_PROVIDER=smtp` delivers to Mailpit. For real delivery:

```bash
EMAIL_PROVIDER=ses
AWS_REGION=us-east-1               # region where your SES identity is verified
AWS_ACCESS_KEY_ID=...              # IAM user or role with ses:SendEmail
AWS_SECRET_ACCESS_KEY=...
EMAIL_FROM=no-reply@yourdomain.com # must be a verified SES identity
```

A new SES account starts in the sandbox, where recipients must also be verified. Request production access in the SES console to send to arbitrary addresses. `EMAIL_PROVIDER=console` is a third option that only logs the messages, useful for tests and CI.

### Switching resume storage to S3 or Cloudflare R2

The default `STORAGE_PROVIDER=local` writes files to `STORAGE_LOCAL_DIR`, which Compose backs with the `resumes` volume. The `s3` adapter uses boto3 and works with any S3-compatible endpoint.

Cloudflare R2:

```bash
STORAGE_PROVIDER=s3
S3_BUCKET=alma-resumes
S3_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com
AWS_REGION=auto
AWS_ACCESS_KEY_ID=<R2 access key id>
AWS_SECRET_ACCESS_KEY=<R2 secret access key>
```

Create the R2 API token in the Cloudflare dashboard under R2 > Manage R2 API Tokens with Object Read & Write on the bucket.

AWS S3:

```bash
STORAGE_PROVIDER=s3
S3_BUCKET=alma-resumes
S3_ENDPOINT_URL=              # leave blank for AWS
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=...         # needs s3:PutObject and s3:GetObject on the bucket
AWS_SECRET_ACCESS_KEY=...
```

With the `s3` adapter, the resume endpoint redirects to a short-lived signed URL. The bucket never needs to be public.

The `AWS_*` variables are shared by the SES and S3 adapters. Using SES on AWS together with R2 storage needs two different key pairs, which is listed as a next step in `docs/DESIGN.md`.

## Tests and linting

Backend tests run against a real Postgres. The simplest path uses the Compose database:

```bash
make test          # starts db if needed, then runs pytest in backend/ via uv
make lint          # ruff, mypy, eslint, tsc
```

Or by hand:

```bash
docker compose up -d db
cd backend
DATABASE_URL=postgresql+asyncpg://alma:alma@localhost:5432/alma uv run pytest
uv run ruff check . && uv run mypy .

cd ../frontend
npm ci && npm run lint && npx tsc --noEmit
```

Tests use fake email and storage adapters, so no Mailpit or disk writes are involved. CI (`.github/workflows/ci.yml`) runs the same commands on every push with a Postgres service container, and validates this repository's compose file.

## Running the API outside Docker

```bash
docker compose up -d db mailpit
cd backend
cp ../.env.example .env
# point at the published ports instead of the compose hostnames
sed -i.bak 's/@db:5432/@localhost:5432/; s/SMTP_HOST=mailpit/SMTP_HOST=localhost/; s#STORAGE_LOCAL_DIR=/data/resumes#STORAGE_LOCAL_DIR=./.resumes#' .env
uv sync
uv run alembic upgrade head
uv run python -m app.seed
uv run uvicorn app.main:app --reload
```

And the web app:

```bash
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

## Repository layout

```
backend/    FastAPI app, adapters, Alembic migrations, tests
frontend/   Next.js app (public form, login, internal leads list)
docs/       PLAN.md (build plan), DESIGN.md (design doc), AGENTS.md (agent usage)
```
