# Coding-Agent Usage

Attribution rules are in `docs/PLAN.md` section 8. Transcript excerpts are submitted separately and are not in this repository.

## Summary

**Tools.** Claude Code running Claude Fable 5.1, inside Conductor so several agents could work in parallel in separate git worktrees. I ran one session as the integrator and spun up the others as needed: four for the build tracks in `docs/PLAN.md` section 7 (backend core, adapters, frontend, ops and docs), then one each for a UI pass, attorney notes, the architecture diagram, and the email design. Agents did their own web research against current Cloudflare and AWS docs to ground the stack decision. Verification used headless Chromium and `curl` against the running Compose stack.

**What I delegated.** Nearly all of the code: the FastAPI service, migrations, adapters, tests, the Next.js app, Docker, CI, and the first draft of every document. Agents are fastest on pattern-heavy work that a test suite or a build can verify, so that is what they got. I also had the integrating session run the merges and the end-to-end checks, because reading an agent's report is not the same as running its code.

**What I did myself.** The decisions and the judgement calls: which stack, which email provider and why (SES over Cloudflare's beta service and over Resend on price), what to leave out of scope, which of fourteen proposed UI improvements were worth the time and which broke the assignment's state machine. I set the interface contracts in the plan, reviewed every branch before it landed, and tested the running app as a user. Every commit is prefixed `[agent]`, `[hand]` or `[agent+edit]`, and `NOTES.md` maps paths to origin.

**Where the agent got it wrong, and how I caught it.** The clearest case is issue 3 below. I gave one agent exact adapter signatures and told another to "define the protocols yourself". Both did exactly as told, and the two halves of the adapter layer could not import each other. The merge produced add/add conflicts in both protocol files. I kept the protocol the routers and thirty tests already used, had the five adapter implementations and forty-four tests rewritten to it, and made the storage stream method async so a missing file raises before any response bytes are sent. The root cause was my prompts. The most instructive case is issue 8: the attorney email linked to a lead page no track had built. Both agents satisfied their own reading of the plan, the merge review confirmed the link existed but never clicked it, and I found the 404 as a user.

**How catches happened.** Two I found directly: by knowing a platform better than the agent (issues 1 and 2) or by using the app (issue 8). The rest surfaced in the merge review I ran on every branch before landing it: re-running tests, lint and types, a real `docker compose up --build`, and a browser click-through, with an agent executing the steps and me deciding what to do with what it found. Three of the eight only showed up there.

## Caught issues

Each entry: what the agent produced, how I caught it, the fix.

**1. Agent claimed FastAPI cannot run on Cloudflare Workers.** During stack selection the agent ruled Cloudflare out because "the assignment mandates FastAPI, which cannot run on Workers." Stale knowledge: Python Workers run FastAPI through Pyodide. I knew the feature existed and pasted the docs link. The agent re-researched and found the real constraint, no native Postgres drivers under Pyodide, so no SQLAlchemy or Alembic. The container decision stood, for the correct reason.

**2. Agent did not know Cloudflare sends transactional email.** It described Cloudflare's email product as receive-only. I pasted the Email Sending docs and asked for research. The agent found it was announced September 2025 and still in public beta with no GA or SLA, and priced SES at $0.10 per thousand against Cloudflare's $0.35 and Resend's $0.90. I chose SES for maturity. Lesson I set for the rest of the build: verify platform capabilities against current docs before ruling an option out.

**3. Two agents built the adapter layer to different contracts.** Track A defined `EmailAdapter.send(EmailMessage)` and `put/delete/stream/presigned_url` with a `create_adapter(settings)` factory per module. Track B implemented `send(to, subject, html, text)`, `put/get_url/open` and `build_*_adapter` factories, and put its fakes in a package where A had a module. Caught in merge review: add/add conflicts in both protocol files. Fix: kept A's protocol, rewrote B's five adapters and their tests, made `stream()` async so a missing key raises `KeyError` before the response starts, merged the fakes, and swapped A's plain-text emails for B's HTML-escaped templates. Commit `a9a41e4`. Lesson: shared interfaces go in the plan verbatim before anyone starts, and every agent gets the same text.

**4. Design doc described code that did not exist.** Track D wrote `docs/DESIGN.md` in parallel with the code and invented plausible names: `EmailSender.send(to, subject, text, html)`, `Storage.url`/`Storage.open`, a `.docx` check on `[Content_Types].xml`, validation "by extension", per-test rollback. None matched the merged code. Caught in merge review by reading the doc against `backend/app`. Fix: five sections corrected; an unverified SES free-tier claim replaced with the wording from the pricing page. Lesson: documentation tracks run after, or are re-verified against, the code they describe.

**5. Frontend Dockerfile copied a directory that did not exist.** The standard Next.js standalone recipe copies `public/`, and the app had none. Local `next build` passed, so Track C never noticed and reported the Dockerfile done. Caught by the first `docker compose up --build` in merge review. Fix: `frontend/public/.gitkeep`. Lesson: "Dockerfile written" is not "image builds"; a `docker build` is now a required gate.

**6. Hand-written OpenAPI spec drifted from the real one.** Track C, with no backend running, wrote `frontend/openapi.json` by hand with schema names, path parameters and operation ids that FastAPI does not emit. The app worked because URLs matched, but the documented regenerate script would have broken the build with six type errors. Caught in merge review by dumping the real spec and diffing. Fix: spec regenerated from the backend, six references updated. The generated-client claim only holds if the spec is actually generated.

**7. CI used a context GitHub rejects at job level.** Track D put `${{ runner.temp }}` in a job-level `env:`; the `runner` context is step-only, so GitHub refused the whole workflow. Track D's gate was "YAML parses", which it did. Caught by the first push to main: a zero-second failed run with no jobs. Fix: `${{ github.workspace }}`. Lesson: a workflow is only verified by a run.

**8. The attorney email linked to a page nobody built.** The plan said the notification links to the lead's page. Track B built the link as `/leads/{id}`; Track C built only the `/leads` list. Merge review confirmed the email contained the link but never followed it. I found it myself: submitted a lead, opened the email in Mailpit, clicked through, got a 404. Fix: a `/leads/[id]` detail page with every field, resume link, and the mark-reached-out action; unauthenticated visits redirect to login and return; bad ids show "Lead not found". Verified by following the real email link in a fresh browser. Lesson: verification has to follow every path the system emits, not just confirm the path exists.

## Delegation ledger

Commit prefixes are the source of truth; this table summarises them. "agent" means agent-written and reviewed by me before merge.

| Work | Who | Why | Commits |
|---|---|---|---|
| Assignment retrieval, stack research (pricing, beta status, limits) | agent, directed by me | Fast fan-out over docs; every number sourced | design phase |
| Stack decisions, scope, interface contracts, `docs/PLAN.md` | me (agent typed the plan from my decisions) | Judgement calls: maturity over novelty, SES over Cloudflare and Resend | `c481c71` |
| Track A: FastAPI core, models, migration, services, routers, auth, seed, 30 tests | agent | Pattern-heavy and test-verifiable; I reviewed the state-transition rule by hand | `721407a` |
| Track B: email and storage adapters, templates, fakes, 44 tests | agent | Thin wrappers over documented SDKs, verifiable with moto and aiosmtpd | `dd62023` |
| Track C: Next.js form, login, list, middleware, generated client, mock, Dockerfile | agent | UI scaffolding is where agents are fastest | `5571092` |
| Track D: Compose, Dockerfile, Makefile, CI, README, DESIGN.md | agent | Boilerplate with a clear spec; design doc then corrected in review (issue 4) | `3810342` |
| Integration: reconcile A and B, rewrite B tests, docs corrections, end-to-end fixes | agent, directed by me | Mechanical once I decided to keep A's protocol (issue 3) | `a9a41e4`, `cc81ddf` |
| Lead detail page (issue 8) | agent, directed by me | Fix for the bug I found as a user | `fe62999` |
| UI pass: history table and timeline, actor email, clickable rows, PDF viewer, tabs, pagination | agent, scoped by me | I approved 8 of 14 proposals; declined undo (breaks the spec's state machine) and search (time) | `75e410a` |
| Attorney notes: append-only table, endpoint, composer, 7 tests | agent, scoped by me | Fixed scope with mandatory gates | `6cdc0c6` |
| Architecture diagram (Archify) | agent, scoped by me | Deterministic tooling with source-path checks beats a hand-drawn box diagram | `a0ad182` |
| Branded HTML email templates | agent, scoped by me | Email-client HTML is fiddly, well specified, and testable in Mailpit | `0acba7b` |

## What was verified before each merge

Every branch: tests, ruff, mypy, alembic check with a downgrade/upgrade round trip where a migration was added; frontend eslint, tsc and `next build`; `docker compose up --build` against the existing database; a browser click-through of the affected screens. Specific to the first full integration: the curl flow covered create lead, fake-PDF rejection (422), unauthenticated list (401), login, transition (200 with actor recorded), repeat and reverse transitions (409), resume bytes identical, resume without cookie (401), logout; Mailpit showed two messages per lead with the attorney mail linking to the lead page and carrying no attachment. Later merges added: following the real email link from Mailpit, migration backfill on live data, notes validation at the 2,000-character boundary, and reading both emails' HTML and text tabs.
