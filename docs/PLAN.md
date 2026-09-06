# Alma Lead Intake — Build Plan

Shared context for every agent working on this repo. Read fully before touching code.
Assignment text: `.context/assignment.md` (or the Ashby link in `docs/ASSIGNMENT.md` once committed).
Deadline: 6 hours from start. Decisions below are FINAL. Do not relitigate stack choices; raise blockers instead.

## 1. What we are building

Lead intake for an immigration law firm.

- Public form (no auth): first name, last name, email, resume/CV upload. All required.
- On submit: persist lead, upload resume, send two emails (confirmation to prospect, notification to attorney).
- Internal UI (auth required): list all leads with every submitted field, view resume, mark lead as reached out.
- Lead state: `PENDING` -> `REACHED_OUT`. Only an authenticated attorney may transition. No other transitions exist.
- REST API: create lead, get lead, list leads, update lead state.

## 2. Stack (decided)

| Layer | Choice | Notes |
|---|---|---|
| API | FastAPI, Python 3.12, uv | Required by assignment |
| DB | Postgres 16, SQLAlchemy 2.0 (async), Alembic | Real migrations; no SQLite |
| Schemas | Pydantic v2 | Separate from ORM models |
| Email | Adapter: `console` / `smtp` (Mailpit) / `ses` (Amazon SES via boto3) | Default local = Mailpit |
| Storage | Adapter: `local` (disk) / `s3` (boto3, endpoint override -> Cloudflare R2, AWS S3, MinIO) | Default local = disk |
| Auth | FastAPI-issued JWT, bcrypt, single seeded attorney user | httpOnly cookie for the web app |
| Web | Next.js 15 App Router, TypeScript, Tailwind, shadcn/ui, react-hook-form + zod | Generated API client from OpenAPI |
| Runtime | Docker Compose: postgres, mailpit, api, web | One command: `docker compose up` |
| CI | GitHub Actions: ruff, mypy, pytest, eslint, tsc | Runs on every push |
| Tests | pytest + httpx AsyncClient, isolated test DB, fake email/storage adapters | |

### Why (short form; long form goes in docs/DESIGN.md)

- Adapters with local defaults mean reviewers need zero secrets to run the whole flow and see both emails in Mailpit.
- SES chosen over Resend (9x cheaper per 1k at scale) and Cloudflare Email Service (public beta since Apr 2026, no GA/SLA). SES has been GA since 2011.
- R2 over S3 for resumes: permanent 10 GB free tier, zero egress, identical boto3 code path. Swappable via env.
- Postgres over DynamoDB/D1: the data is relational, the list view needs filtering/sorting, and reviewers know the tooling.
- Container over Cloudflare Python Workers: Pyodide cannot run psycopg/asyncpg, so no SQLAlchemy/Alembic. ASGI app ports later if that changes.

### Explicitly out of scope (list in DESIGN.md "next steps")

Kubernetes, Terraform, message queue, rate limiting, multi-tenant auth, admin user management, pagination beyond basic limit/offset.

## 3. Repo layout

```
.
├── docker-compose.yml
├── Makefile                  # make up / down / test / lint / migrate / seed
├── .env.example              # every var documented, safe defaults
├── .github/workflows/ci.yml
├── README.md                 # how to run locally (deliverable)
├── NOTES.md                  # agent vs hand-written attribution (deliverable)
├── docs/
│   ├── PLAN.md               # this file
│   ├── DESIGN.md             # design doc (deliverable)
│   └── AGENTS.md             # coding-agent usage writeup (deliverable)
├── private/                  # gitignored; transcripts live here, submitted via Ashby not git
│   └── transcripts/
├── backend/
│   ├── pyproject.toml
│   ├── alembic/
│   ├── app/
│   │   ├── main.py           # app factory, routers, middleware
│   │   ├── core/             # config (pydantic-settings), security, logging
│   │   ├── db/               # engine, session, base
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic request/response
│   │   ├── repositories/     # DB access only
│   │   ├── services/         # business logic, state transitions
│   │   ├── adapters/
│   │   │   ├── email/        # base.py, console.py, smtp.py, ses.py
│   │   │   └── storage/      # base.py, local.py, s3.py
│   │   └── api/
│   │       ├── deps.py       # auth + DI
│   │       └── v1/           # leads.py, auth.py, health.py
│   └── tests/
└── frontend/
    ├── app/
    │   ├── page.tsx          # public lead form
    │   ├── login/
    │   └── (internal)/leads/ # auth-guarded list, plus [id]/ detail page (target of the attorney email link)
    ├── components/
    ├── lib/api/              # generated client
    └── middleware.ts         # cookie check for /leads
```

## 4. Data model

```
leads
  id           uuid pk
  first_name   text not null
  last_name    text not null
  email        text not null
  resume_key   text not null        -- storage key, never a raw path/URL
  resume_name  text not null        -- original filename
  resume_type  text not null        -- mime
  state        enum('PENDING','REACHED_OUT') not null default 'PENDING'
  created_at   timestamptz not null default now()
  updated_at   timestamptz not null
  reached_out_at timestamptz null
  reached_out_by uuid null fk users.id

users
  id            uuid pk
  email         text unique not null
  password_hash text not null
  created_at    timestamptz
```

## 5. API (v1)

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | /api/v1/leads | none | multipart: fields + resume. Returns 201 + lead |
| GET | /api/v1/leads | JWT | list, `?state=&limit=&offset=`; response also carries global `counts` per state |
| GET | /api/v1/leads/{id} | JWT | single lead plus `events` (history, oldest first) |
| PATCH | /api/v1/leads/{id}/state | JWT | body `{state: "REACHED_OUT"}`; 409 on invalid transition |
| GET | /api/v1/leads/{id}/resume | JWT | 302 to signed URL (s3) or streams file (local); inline by default, `?download=true` forces a save |
| POST | /api/v1/auth/login | none | sets httpOnly cookie, returns user |
| POST | /api/v1/auth/logout | JWT | clears cookie |
| GET | /api/v1/auth/me | JWT | current user `{id, email}` (added by Track A for the web app) |
| GET | /api/v1/health | none | db check |

Response shapes (fixed by Track A):
- Lead: `{id, first_name, last_name, email, resume_name, resume_type, state, created_at, updated_at, reached_out_at, reached_out_by, reached_out_by_email}`. `resume_key` is never exposed.
- Lead event: `{id, from_state, to_state, actor_id, actor_email, created_at}`; `from_state` and the actor fields are null for the prospect's submission.
- List: `{items: Lead[], total, limit, offset, counts: {pending, reached_out}}`; `limit` 1..200 (default 50), `offset` >= 0. `counts` are global, independent of the `state` filter.
- Auth cookie is named `access_token`; `Authorization: Bearer <jwt>` is accepted too.
- Adapter selection: `app/adapters/<email|storage>/<provider>.py` must expose `create_adapter(settings)`; `api/deps.py` imports it by `EMAIL_PROVIDER` / `STORAGE_PROVIDER`.

Rules:
- Resume: pdf/doc/docx only, max 5 MB, validated by magic bytes not just extension.
- Emails are sent via FastAPI `BackgroundTasks` AFTER the lead is committed. Email failure is logged, never fails the request.
- Attorney email links to the internal lead page; it does NOT attach the resume.
- State transition is a service-layer method `mark_reached_out(lead, user)`; anything else raises `InvalidTransition` -> 409.

## 6. Environment variables (.env.example)

```
DATABASE_URL=postgresql+asyncpg://alma:alma@db:5432/alma
JWT_SECRET=change-me
ATTORNEY_EMAIL=attorney@example.com          # notification recipient
SEED_USER_EMAIL=attorney@example.com         # login for internal UI
SEED_USER_PASSWORD=password123
EMAIL_PROVIDER=smtp                           # console | smtp | ses
SMTP_HOST=mailpit
SMTP_PORT=1025
EMAIL_FROM=no-reply@example.com
AWS_REGION=us-east-1                          # ses + s3
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
STORAGE_PROVIDER=local                        # local | s3
STORAGE_LOCAL_DIR=/data/resumes
S3_BUCKET=
S3_ENDPOINT_URL=                              # set for R2/MinIO, blank for AWS
PUBLIC_WEB_URL=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000
```

No secrets are ever committed. Reviewers run with defaults and need no cloud account.

## 7. Work split (parallel-safe)

Each track owns its directories; do not edit another track's files without coordinating in `.context/`.

- **Track A — backend core:** config, db, models, alembic, repositories, services, leads + auth routers, tests.
- **Track B — adapters:** email (console/smtp/ses), storage (local/s3), fakes for tests.
- **Track C — frontend:** form, login, leads list, middleware, generated client.
- **Track D — ops + docs:** docker-compose, Makefile, CI, README, DESIGN.md, AGENTS.md, NOTES.md.

Integration contract between tracks is Section 5 (API) and Section 6 (env). Change either only by updating this file first.

## 8. Agent usage rules (applies to every agent)

- Every commit message ends with `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>` when an agent wrote the bulk of it.
- Commit subject prefix: `[agent]` agent-written, `[hand]` human-written, `[agent+edit]` agent draft with human fixes.
- When a human catches an agent bug, log it in `docs/AGENTS.md` under "Caught issues" immediately: what, how found, fix commit.
- Save representative prompts/responses to `private/transcripts/` as you go, not at the end. That folder is gitignored: transcripts are private and are uploaded directly to Ashby, never committed. Do not paste raw transcript text into any tracked file.
- Do not fabricate attribution. If unsure, mark `[agent+edit]`.
