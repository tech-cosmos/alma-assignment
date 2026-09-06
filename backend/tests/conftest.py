import asyncio
import os
from collections.abc import AsyncIterator, Iterator
from urllib.parse import urlsplit

import asyncpg
import httpx
import pytest
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from alembic import command
from app.core.config import Settings, get_settings
from app.core.security import hash_password
from app.models.user import User
from tests.fakes import FakeEmailAdapter, FakeStorageAdapter

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+asyncpg://alma:alma@localhost:5432/alma_test"
)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
TEST_SECRET = "test-secret-that-is-at-least-32-bytes-long"
os.environ["JWT_SECRET"] = TEST_SECRET
os.environ["ATTORNEY_EMAIL"] = "attorney@example.com"
os.environ["PUBLIC_WEB_URL"] = "http://web.test"
get_settings.cache_clear()

ATTORNEY_EMAIL = "attorney@example.com"
ATTORNEY_PASSWORD = "password123"


async def _ensure_database() -> None:
    parts = urlsplit(TEST_DATABASE_URL.replace("+asyncpg", ""))
    dbname = parts.path.lstrip("/")
    conn = await asyncpg.connect(
        host=parts.hostname,
        port=parts.port,
        user=parts.username,
        password=parts.password,
        database="postgres",
    )
    try:
        exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", dbname)
        if not exists:
            await conn.execute(f'CREATE DATABASE "{dbname}"')
    finally:
        await conn.close()


@pytest.fixture(scope="session", autouse=True)
def migrated_database() -> Iterator[None]:
    """Create the test database and apply migrations once per session (sync: no loop running)."""
    asyncio.run(_ensure_database())
    cfg = Config("alembic.ini")
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")
    yield


@pytest.fixture(scope="session")
def settings() -> Settings:
    return get_settings()


@pytest.fixture(scope="session")
async def engine(settings: Settings) -> AsyncIterator[AsyncEngine]:
    from app.db.session import create_engine

    engine = create_engine(settings.database_url)
    yield engine
    await engine.dispose()


@pytest.fixture(autouse=True)
async def clean_tables(engine: AsyncEngine) -> AsyncIterator[None]:
    yield
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE lead_events, leads, users"))


@pytest.fixture
def email_adapter() -> FakeEmailAdapter:
    return FakeEmailAdapter()


@pytest.fixture
def storage_adapter() -> FakeStorageAdapter:
    return FakeStorageAdapter()


@pytest.fixture
async def client(
    engine: AsyncEngine, email_adapter: FakeEmailAdapter, storage_adapter: FakeStorageAdapter
) -> AsyncIterator[httpx.AsyncClient]:
    from app.api.deps import get_email_adapter, get_storage_adapter
    from app.db.session import create_session_factory
    from app.main import create_app

    app = create_app()
    app.state.engine = engine
    app.state.session_factory = create_session_factory(engine)
    app.dependency_overrides[get_email_adapter] = lambda: email_adapter
    app.dependency_overrides[get_storage_adapter] = lambda: storage_adapter
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
async def attorney(engine: AsyncEngine) -> User:
    from app.db.session import create_session_factory

    async with create_session_factory(engine)() as session:
        user = User(email=ATTORNEY_EMAIL, password_hash=hash_password(ATTORNEY_PASSWORD))
        session.add(user)
        await session.commit()
        return user


@pytest.fixture
async def auth_client(client: httpx.AsyncClient, attorney: User) -> httpx.AsyncClient:
    resp = await client.post(
        "/api/v1/auth/login", json={"email": ATTORNEY_EMAIL, "password": ATTORNEY_PASSWORD}
    )
    assert resp.status_code == 200, resp.text
    assert "access_token" in client.cookies
    return client


@pytest.fixture
async def db_session(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    from app.db.session import create_session_factory

    async with create_session_factory(engine)() as session:
        yield session
