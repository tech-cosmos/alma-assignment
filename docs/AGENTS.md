# Coding-Agent Usage

This document is a required deliverable. It is maintained continuously during the build, not written at the end.
See `docs/PLAN.md` section 8 for the attribution rules every agent follows.

## Tools used

- Claude Code (Claude Fable 5.1) run inside Conductor, with several workspaces working in parallel on the tracks defined in `docs/PLAN.md` section 7.
- Web lookups by the agent (Cloudflare and AWS docs, pricing pages) to ground design decisions in current facts.

## What was delegated vs. written by hand

_Filled in as tracks complete. See the delegation ledger at the end._

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

**Lesson applied going forward:** the agent must verify platform capabilities against current docs before ruling an option out, especially for fast-moving platforms. This is now the working rule for the rest of the build.

## Delegation ledger

| Task | Who | Why |
|---|---|---|
| Assignment retrieval and summary | agent | Mechanical, verifiable against the source |
| Stack research (pricing, beta status, limits) | agent, directed by Shivam | Fast fan-out over docs; every number was sourced |
| Stack decisions | Shivam | Judgement calls: maturity over novelty, SES over Cloudflare/Resend |
| `docs/PLAN.md` | agent from Shivam's decisions | Structured write-up of agreed decisions |

## Transcript excerpts

Prompt logs and session transcripts are private and are not committed to this repository. They are submitted separately through the Ashby assignment upload.
