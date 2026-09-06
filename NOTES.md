# NOTES — attribution of agent vs. hand-written work

Commit subjects are prefixed `[agent]`, `[hand]`, or `[agent+edit]`. Agent-authored commits carry a `Co-Authored-By` trailer.
Run `git log --oneline` to see the split; `scripts/agent_stats.sh` (added later) summarises it.

| Path | Origin | Notes |
|---|---|---|
| docs/PLAN.md | agent | Written by the agent from decisions Shivam made in discussion |
| docs/ASSIGNMENT.md | agent | Verbatim copy of the assignment text |
| docs/AGENTS.md | agent | Log maintained by agent; catch entries describe Shivam's corrections |
| backend/ (all) | agent | Track A commit `721407a`; adapters from Track B `dd62023`, reconciled by the integrating agent in `a9a41e4` |
| frontend/ (all) | agent | Track C commit `5571092` |
| docker-compose.yml, backend/Dockerfile, Makefile, .github/, .env.example, README.md, docs/DESIGN.md | agent | Track D commit `3810342`; DESIGN.md corrected during merge review |
| backend/.dockerignore | agent | Added during Track D review |
| frontend/public/.gitkeep, frontend/openapi.json, frontend/lib/api/schema.d.ts, frontend/lib/api/index.ts, frontend/lib/api/mock.ts | agent | Fixed during integration (caught issues 5 and 6); spec regenerated from the running backend |
