# syntax=docker/dockerfile:1.7
# Backend image: FastAPI on Python 3.12, dependencies managed by uv.
#
# Expectations on the backend project (Track A):
#   - backend/pyproject.toml (+ uv.lock, commit it for reproducible builds)
#   - ASGI app importable as `app.main:app`
#   - Alembic configured via backend/alembic.ini, migrations in backend/alembic/
#   - `python -m app.seed` idempotently creates the attorney user from SEED_USER_*
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Install dependencies first so the layer is cached until pyproject/lock change.
COPY pyproject.toml uv.lock* ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --no-install-project

# Then the application itself.
COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev

# Run as an unprivileged user; /data/resumes is the default STORAGE_LOCAL_DIR.
RUN useradd --system --uid 10001 --home /app appuser \
    && mkdir -p /data/resumes \
    && chown -R appuser:appuser /app /data/resumes
USER appuser

EXPOSE 8000

# Migrate, seed the attorney login, then serve. Failure of any step stops the container,
# which is what we want: a half-migrated API should not come up.
CMD ["sh", "-c", "alembic upgrade head && python -m app.seed && exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]
