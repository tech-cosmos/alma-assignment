# Coding-Agent Usage

This document is a required deliverable. The first section is the half-page writeup the assignment asks for. Everything after it is the supporting record: every agent mistake we caught, the delegation ledger, and what was verified before each merge. It was maintained during the build, not written at the end. Attribution rules are in `docs/PLAN.md` section 8.

## Summary (the half-page writeup)

**Tools.** Claude Code running Claude Fable 5.1, inside Conductor so that several agents could work in parallel in separate git worktrees. One agent acted as integrator; four built the tracks in `docs/PLAN.md` section 7 (backend core, adapters, frontend, ops and docs); a sixth did a UI pass after the first end-to-end run. Agents did their own web research against current Cloudflare and AWS docs to ground the stack decision.

**What was delegated.** Nearly all of the code: the FastAPI service, migrations, adapters, tests, the Next.js app, Docker, CI, and the first drafts of every document. Agents are fastest on pattern-heavy work that a test suite or a build can verify, so that is what they got. The integrating agent also did the merges and the end-to-end verification, because reading five agents' reports is not the same as running their code.

**What I did myself.** The decisions and the judgement calls: which stack, which email provider and why (SES over Cloudflare's beta service and over Resend on price), what to leave out of scope, which of the fourteen proposed UI improvements were worth the time and which broke the assignment's state machine. I set the interface contracts in the plan, reviewed every merge before it landed, and tested the running app as a user. Two of the eight logged catches were mine; the other six the integrating agent found before I saw them. Every commit is prefixed `[agent]`, `[hand]` or `[agent+edit]`, and `NOTES.md` maps paths to origin.

**Where the agent got it wrong.** The clearest case is caught issue 3. I gave one agent exact adapter signatures and told another to "define the protocols yourself". Both did exactly as told, and the two halves of the adapter layer could not import each other: different method names, different factory conventions, a fakes module in one branch and a fakes package in the other. The merge produced add/add conflicts in both protocol files. The fix was to keep the protocol the routers and thirty tests already used, rewrite the five adapter implementations and their forty-four tests to it, and make the storage stream method async so a missing file raises before any response bytes are sent. The root cause was my prompts, not the agents, and the lesson is recorded: shared interfaces go in the plan verbatim before anyone starts. The most instructive case is issue 8: the attorney email linked to a lead page that no track had built. Both agents satisfied their own reading of the plan, the integrator confirmed the link existed but never clicked it, and I found the 404 as a user.

**Verification.** Nothing was merged on the strength of an agent's report. Each track was re-run locally: tests, lint, types, migrations, a real `docker compose up --build`, and a browser click-through including the paths the emails emit. Three of the eight catches only surfaced there.

## Tools used

- Claude Code (Claude Fable 5.1) run inside Conductor, with several workspaces working in parallel on the tracks defined in `docs/PLAN.md` section 7.
- Web lookups by the agent (Cloudflare and AWS docs, pricing pages) to ground design decisions in current facts.
- Headless Chromium via `agent-browser` for the browser verification passes, and `curl` against the compose stack for the API passes.

## Caught issues

Each entry: what the agent produced, why it was wrong, how it was caught, and the fix.

### 1. Agent claimed FastAPI cannot run on Cloudflare Workers (design phase)

- **What the agent said:** While comparing backends, the agent stated Cloudflare was a poor fit because "the assignment mandates FastAPI, which cannot run on Workers."
- **Why it was wrong:** Cloudflare Python Workers support FastAPI through Pyodide with a built-in ASGI server and the `pywrangler` CLI. The agent's knowledge was stale.
- **How it was caught:** Shivam knew the feature existed and pasted the docs link (developers.cloudflare.com/workers/languages/python/packages/fastapi/).
- **Fix:** The agent fetched the current docs, confirmed support, and re-evaluated. The real constraints turned out to be narrower: Pyodide cannot run native DB drivers (psycopg/asyncpg), so SQLAlchemy and Alembic are unavailable. The container-based FastAPI decision stood, but for the correct reason. Recorded in `docs/PLAN.md` section 2.

### 2. Agent did not know Cloudflare offers transactional email sending (design phase)

- **What the agent said:** The agent asserted Cloudflare's email product was "built for receiving, not sending" and that the send binding only delivers to verified addresses on your zone, so a third-party provider would be required regardless.
- **Why it was wrong:** Cloudflare Email Service includes Email Sending (REST API, SMTP, and Workers binding) to arbitrary recipients on the Workers Paid plan. The agent was describing the pre-2025 Email Routing product.
- **How it was caught:** Shivam pasted the Email Service "send emails" docs link and asked the agent to research and confirm.
- **Fix:** The agent fetched the docs, pricing, limits, and launch timeline. Finding: Email Sending was announced Sept 2025, private beta Nov 2025, public beta Apr 16 2026, and still beta with no GA or SLA. Shivam decided on Amazon SES for maturity; the agent's price research (SES $0.10/1k vs Cloudflare $0.35/1k vs Resend $0.90/1k) supported that choice. Recorded in `docs/PLAN.md` section 2.
- **Lesson (from issues 1 and 2):** verify platform capabilities against current docs before ruling an option out, especially for fast-moving platforms. This became the working rule for the rest of the build.

### 3. Tracks A and B built the adapter layer to two different contracts (build phase)

- **What the agents produced:** Track A defined `EmailAdapter.send(message: EmailMessage)` and a storage protocol of `put/delete/stream/presigned_url`, with each provider module exposing `create_adapter(settings)`. Track B, working in parallel, implemented `send(to, subject, html, text)` and `put/get_url/open` with `build_*_adapter(provider, ...)` factories, and shipped its fakes as a `tests/fakes/` package while Track A had `tests/fakes.py`. Neither branch could import the other's work.
- **Why it was wrong:** Root cause was the integrator's prompts, not the track agents. Track B's prompt spelled out concrete signatures while Track A's prompt said "define the protocols yourself". Both agents followed their instructions exactly. Track B also started before Track A had pushed, so there was no `base.py` to match.
- **How it was caught:** Merging B onto A produced add/add conflicts in both `base.py` files, and the merged test suite would not have imported. Caught by the integrating session before running anything.
- **Fix:** Kept Track A's protocols (the routers, services and 30 tests already used them) and adapted Track B's five implementations to them. `stream()` was made `async` so a missing key raises `KeyError` before any response bytes are sent. Track B's `build_*` factories were replaced by `create_adapter(settings)` in each module, matching the importlib loader in `app.api.deps`. The two fakes were merged into one package with A's API plus B's call recording. Track B's HTML-escaped templates replaced Track A's plain-text emails. Commit `a9a41e4`.
- **Lesson:** When parallel tracks share an interface, put the exact signatures in the shared plan before anyone starts, and give every agent the same text.

### 4. Design doc described interfaces and validation logic that did not exist (build phase)

- **What the agent produced:** Track D wrote `docs/DESIGN.md` in parallel with the code and described an `EmailSender.send(to, subject, text, html)` interface, `Storage.url`/`Storage.open` methods, fakes named `FakeEmailSender`/`FakeStorage`, a `.docx` check based on `[Content_Types].xml`, validation "by extension", and per-test rollback. None of those matched the merged code: the real protocol is `EmailAdapter.send(EmailMessage)`, storage is `put/delete/stream/presigned_url`, `.docx` is detected by a `word/document.xml` entry, the extension is ignored entirely, and tests truncate rather than roll back.
- **Why it was wrong:** Track D had no code to read, so it wrote plausible names from the plan and the prompt. A design doc that contradicts the code is worse than a thin one, because a reviewer who opens both will trust neither.
- **How it was caught:** Line-by-line read of `DESIGN.md` against `backend/app` during the Track D merge review.
- **Fix:** Sections 2, 5, 6, 11 and 12 corrected to the real names and behaviour, and an adapter unit-test line added. The unverified SES "3,000 free per month for 12 months" claim was replaced with the credits wording from the pricing page fetched during design. Commit follows the Track C merge.
- **Lesson:** Documentation tracks should run after, or be re-verified against, the code they describe.

### 5. Frontend Dockerfile copied a directory that did not exist (build phase)

- **What the agent produced:** Track C's `frontend/Dockerfile` has `COPY --from=builder /app/public ./public`, the standard Next.js standalone recipe. The app has no `public/` directory (fonts are vendored under `app/fonts`), so `docker compose up --build` failed on the `web` image with "/app/public: not found". Track C reported the Dockerfile as done and noted it "matches what Track D's compose already assumes", but had never run the build.
- **Why it was wrong:** A copied recipe was not checked against the project it was copied into. Local `next build` succeeded, so nothing in Track C's own gates exercised the Dockerfile.
- **How it was caught:** First `docker compose up --build` during integration.
- **Fix:** Added `frontend/public/.gitkeep` so the directory exists and the recipe stays standard for future static assets. Image builds and the `web` container serves on port 3000.
- **Lesson:** "Dockerfile written" is not "image builds". Track prompts should require `docker build` as a gate whenever a Dockerfile is part of the deliverable.

### 6. Frontend's hand-written OpenAPI spec drifted from the real one (build phase)

- **What the agent produced:** Track C, working without a running backend, wrote `frontend/openapi.json` by hand with schema names `LeadOut`/`UserOut`, path parameter `{id}` and operation id `list_leads`. FastAPI actually emits `LeadRead`/`UserRead`, `{lead_id}` and `list_leads_api_v1_leads_get`. The app worked at runtime because the URLs are identical, but the documented `npm run openapi:pull` workflow would have regenerated the types and broken the build with six type errors.
- **Why it was wrong:** The generated-client claim in the design only holds if the spec is actually generated. A hand-written spec that diverges silently is a trap for the next person who runs the pull script.
- **How it was caught:** Integration dumped the real spec from `app.openapi()`, diffed the schema and path lists, then ran the regeneration and `tsc`.
- **Fix:** Replaced `frontend/openapi.json` with the backend's real output, regenerated `schema.d.ts`, and updated the six references in `lib/api/index.ts` and `lib/api/mock.ts`. `tsc`, `eslint` and `next build` pass on the regenerated types.

### 7. CI workflow used a context GitHub does not allow at job level (build phase)

- **What the agent produced:** Track D's `ci.yml` set `STORAGE_LOCAL_DIR: ${{ runner.temp }}/resumes` in the backend job's `env:` block. The `runner` context is only available inside steps, so GitHub rejected the whole workflow before starting any job. Track D's own gate was "the workflow file parses as YAML", which it did; the error is in GitHub's expression rules, not YAML.
- **How it was caught:** First push to `main` showed a 0-second failed run with "This run likely failed because of a workflow file issue" and no jobs.
- **Fix:** Use `${{ github.workspace }}/.ci-resumes`, which is valid at job level. Re-pushed and watched the run.
- **Lesson:** A workflow is only verified by a run. Local YAML validation and `actionlint` catch different classes of error; neither substitutes for the first green run.

### 8. The attorney email linked to a page nobody built (found by Shivam in the running app)

- **What the agents produced:** The plan says the attorney notification links to the lead's internal page. Track B built the link as `PUBLIC_WEB_URL/leads/{id}`, exactly as specified. Track C built the internal UI as a single list at `/leads` and never created a `/leads/[id]` route. Both agents satisfied their own reading of the plan; the plan itself never listed a detail page in the frontend routes.
- **Why the integrator missed it:** The end-to-end check verified that the attorney email *contained* the lead link, and separately that `/leads` worked after login. It never clicked the link. Checking that a link exists is not the same as following it.
- **How it was caught:** Shivam submitted a lead, opened the notification in Mailpit, clicked through, and got the Next.js 404 page.
- **Fix:** Added `app/(internal)/leads/[id]/page.tsx` with a `LeadDetail` client component: loads the lead through the existing get endpoint, shows every field, links the resume, and offers the same "Mark reached out" action as the list. A 404 or malformed id shows a "Lead not found" message with a way back; a 401 clears the cookie and redirects to login with the detail page as `next`. Names in the list now link to the detail page, and the state badge moved to a shared component. Verified by clicking the actual Mailpit link in a fresh browser session, logging in, landing on the detail page, and marking the lead reached out.
- **Lesson:** Verification has to follow every user-facing path the system emits, not just confirm the path exists. Links in emails are user-facing paths.


## Delegation ledger

One row per unit of work. `Who` is one of `agent`, `Shivam`, or `agent, directed by Shivam` (agent draft with human review or fixes). `Why` explains the choice of who did it, not what it is. Rows are added by whoever merges the work, from commit history and the track's own notes; nothing is added speculatively.

### Design phase

| Task | Who | Why |
|---|---|---|
| Assignment retrieval and summary | agent | Mechanical, verifiable against the source |
| Stack research (pricing, beta status, limits) | agent, directed by Shivam | Fast fan-out over docs; every number was sourced |
| Stack decisions | Shivam | Judgement calls: maturity over novelty, SES over Cloudflare/Resend |
| `docs/PLAN.md` | agent from Shivam's decisions | Structured write-up of agreed decisions |

### Build phase

Filled in per track as each track branch is reviewed and merged (`docs/PLAN.md` section 7). Commit prefixes (`[agent]`, `[hand]`, `[agent+edit]`) are the source of truth; this table summarises them.

| Track | Task | Who | Why | Commits |
|---|---|---|---|---|
| A | FastAPI core: config, models, migration, repositories, services, routers, auth, seed, 30 tests | agent | Pattern-heavy and fully test-verifiable; the state transition rule was reviewed by hand at merge | `721407a` |
| B | Email adapters (console, smtp, ses), storage adapters (local, s3), templates, fakes, 44 tests | agent | Thin wrappers over well-documented SDKs; moto and aiosmtpd make them verifiable without credentials | `dd62023` |
| C | Next.js form, login, leads list, middleware, generated client, mock API, Dockerfile | agent | UI scaffolding is where agents are fastest; verified with tsc, eslint, build and a browser run against the real API | `5571092` |
| D | Compose, Dockerfile, Makefile, CI, .env.example, README, DESIGN.md | agent | Boilerplate with a clear spec; the design doc was then corrected by hand-directed review (caught issue 4) | `3810342` |
| Integration | Reconcile A and B adapter contracts, rewrite B tests, wire templates into the notifier | agent, directed by Shivam | Mechanical once the decision (keep A's protocol) was made; decision reasoning is in caught issue 3 | `a9a41e4` |
| UI pass | Lead history table and timeline, actor email, clickable rows, inline PDF viewer with download flag, signed-in user, pagination, filter tabs with counts, relative times, detail page restructure | agent, scoped by Shivam with the integrator's review | Shivam picked 8 of 14 proposed items; undo of the state transition and search were declined to stay within the assignment's state machine and the time box | `75e410a` |
| Integration | Design doc corrections, `.dockerignore`, end-to-end verification | agent, directed by Shivam | Verification against running containers, not reports | see verification table |
| Notes | Attorney notes on leads: `lead_notes` table and migration 0003, append-only POST endpoint, notes in the detail response, 7 tests, composer and merged timeline on the lead page, regenerated spec, mock API, docs | agent, scoped by Shivam | Fixed scope with explicit gates; the one judgement call (the frontend's 422 field mapping dropped a field named `body`) is recorded in the commit | `6cdc0c6` |

Tracks: A backend core, B adapters, C frontend, D ops and docs.

### Verification and merge

What the human checked before merging each track, and what was changed as a result. Anything that turns out to be a bug goes under "Caught issues" above instead.

| Track | Checked by | What was verified | Outcome |
|---|---|---|---|
| A | integrating agent, on Shivam's behalf | `uv run pytest` (30 pass), `ruff check`, `ruff format --check`, `mypy --strict`, `alembic check` against a live Postgres 17 | Merged as-is |
| B | integrating agent | Read every adapter and test; attempted merge onto A | Contract mismatch found (caught issue 3); adapters and tests rewritten; merged suite 80 pass, ruff, mypy clean |
| D | integrating agent | `docker compose config`, Dockerfile expectations vs Track A (`app.main:app`, `alembic.ini`, `python -m app.seed`, `/api/v1/health`), CI YAML, README commands, DESIGN.md vs code | DESIGN.md drift (caught issue 4) fixed; `backend/.dockerignore` added so `COPY . .` cannot pull a host `.venv` into the image |
| C | integrating agent | `npm ci`, `eslint`, `tsc --noEmit`, `next build`; read middleware, API client and error mapping against the section 5 contract | Merged; end-to-end run against the real API recorded below |
| Compose end-to-end (API) | integrating agent | `docker compose up --build`; curl: health, create lead with PDF (201), fake PDF (422), list without cookie (401), login, list (envelope), PATCH to REACHED_OUT (200 with `reached_out_at`/`reached_out_by`), repeat (409), reverse (409), resume download bytes identical with correct headers, resume without cookie (401), state filter, logout then list (401). Mailpit: two messages per lead, attorney mail links to `/leads/{id}` with no attachment | Web image failed to build (caught issue 5); fixed, then every step passed |
| Email link to detail page | Shivam, then integrating agent | Clicked the attorney notification link in Mailpit: 404 (caught issue 8). After the fix: fresh browser session follows the email link, is redirected to login with `next` set, lands on the detail page after login, marks the lead reached out; bogus id shows "Lead not found" | Fixed and re-verified |
| UI pass | integrating agent | Snapshot of the uncommitted work from its workspace; backend ruff, mypy, 80 tests, `alembic check` and a 0002 downgrade/upgrade round trip; frontend eslint, tsc, `next build`; `docker compose up --build` against the existing database to confirm the migration backfills; browser click-through of tabs, counts, row click, history timeline, PDF viewer, mark reached out, download flag | Merged after the plan's list-response line was updated to include `counts` |
| Notes | agent, on Shivam's behalf | Backend: ruff, ruff format, mypy, 87 tests, `alembic check`, 0002 downgrade then upgrade head round trip against the temp cluster. Frontend: `openapi:pull` from a live API (not hand-edited), eslint, tsc, `next build`. `docker compose up --build` migrated the existing database to 0003. Headless Chromium: detail page redirected to login with `next`, logged in, "Add note" disabled while empty and for whitespace, posted a note and saw it in the timeline with the attorney email and its own dot colour without a reload, reloaded and it persisted, server returned 422 for empty, whitespace-only and 2,001-character bodies | Passed; the 422 field-error rendering was not exercised in the browser because the composer never sends a body the server would reject |
| Compose end-to-end (browser) | integrating agent | Headless Chromium via agent-browser: submitted the public form with a PDF, saw the "Received" state; `/leads` redirected to `/login?next=/leads`; logged in; both leads listed with resume links to the API; clicked "Mark reached out", button became disabled "Reached out"; no console or page errors | Passed. Frontend spec drift (caught issue 6) fixed afterwards and re-verified with `tsc`, `eslint`, `next build` |

## Transcript excerpts

Prompt logs and session transcripts are private and are not committed to this repository. They are submitted separately through the Ashby assignment upload.
