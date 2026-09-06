# backend

FastAPI service for lead intake. See `docs/PLAN.md` for the contract.

```sh
uv sync --all-groups                 # Python 3.12 (.python-version)
uv run alembic upgrade head          # DATABASE_URL from env / .env
uv run seed                          # creates SEED_USER_EMAIL / SEED_USER_PASSWORD attorney
uv run uvicorn app.main:app --reload # http://localhost:8000/docs
```

Quality gates (all must pass):

```sh
uv run ruff check . && uv run ruff format --check .
uv run mypy
TEST_DATABASE_URL=postgresql+asyncpg://alma:alma@localhost:5432/alma_test uv run pytest
```

Tests create the test database if missing, run the Alembic migrations, and truncate tables
between tests. They use in-memory fake adapters from `tests/fakes.py`; no email or storage
provider is needed.

Adapters are selected by `EMAIL_PROVIDER` / `STORAGE_PROVIDER`. Each provider is a module
`app/adapters/<kind>/<provider>.py` exposing `create_adapter(settings)`; see the protocol
docstrings in `app/adapters/*/base.py`.
