import asyncio
import os

import asyncpg
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

from app.app import app
from app.database import get_session
from app.models.models import Base
from app.settings import settings

_db_host = "localhost"
_db_user = settings.db_username or "test"
_db_pass = settings.db_password or "postgres"
_db_name = os.environ.get(
    "TEST_DB_NAME",
    f"{settings.db_database}_test" if settings.db_database else "crispy_finance_test",
)

TEST_DB_URL = os.environ.get(
    "TEST_DB_URL",
    f"postgresql+asyncpg://{_db_user}:{_db_pass}@{_db_host}/{_db_name}",
)

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()

async def _ensure_test_db_exists() -> None:
    conn = await asyncpg.connect(
        host=_db_host,
        user=_db_user,
        password=_db_pass,
        database="postgres",
    )
    try:
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", _db_name
        )
        if not exists:
            await conn.execute(f'CREATE DATABASE "{_db_name}"')
    finally:
        await conn.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    await _ensure_test_db_exists()
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def clean_db(setup_db: AsyncEngine):
    yield
    async with AsyncSession(setup_db, expire_on_commit=False) as s:
        await s.execute(
            text("TRUNCATE TABLE transaction_entries, transactions, accounts RESTART IDENTITY CASCADE")
        )
        await s.commit()


@pytest_asyncio.fixture
async def client(setup_db: AsyncEngine):
    async def override_get_session():
        async with AsyncSession(setup_db, expire_on_commit=False) as s:
            yield s

    app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as c:
        yield c

    app.dependency_overrides.clear()