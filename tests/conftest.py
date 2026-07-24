from collections.abc import AsyncIterator, Iterator
import os

from fastapi.testclient import TestClient
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app import models as _models  # noqa: F401
from app.core.cache import init_cache
from app.db import database
from app.db.database import Base
from app.main import app
from tests.seed import ADMIN_EMAIL, ADMIN_PASSWORD, seed_db

API_PREFIX = "/api/v1"
EXTRA_SCHEMAS = ("auth",)


def _async_database_url(url: str) -> str:
    if url.startswith("postgresql+asyncpg://"):
        return url
    if url.startswith("postgresql+psycopg2://"):
        return url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


@pytest.fixture(scope="session")
def database_url() -> Iterator[str]:
    external = os.getenv("TEST_DATABASE_URL")
    if external:
        yield _async_database_url(external)
        return

    from testcontainers.postgres import PostgresContainer

    with PostgresContainer("postgres:16-alpine") as postgres:
        yield _async_database_url(postgres.get_connection_url())


@pytest_asyncio.fixture(scope="session")
async def test_engine(database_url: str) -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(database_url, poolclass=NullPool)

    async with engine.begin() as connection:
        for schema in EXTRA_SCHEMAS:
            await connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
        await connection.run_sync(Base.metadata.create_all)

    database.AsyncSessionLocal.configure(bind=engine)

    yield engine

    async with engine.begin() as connection:
        for table in Base.metadata.tables.values():
            name = f'"{table.schema}"."{table.name}"' if table.schema else f'"{table.name}"'
            await connection.execute(text(f"DROP TABLE IF EXISTS {name} CASCADE"))
    await engine.dispose()


async def _truncate_all_tables(engine: AsyncEngine) -> None:
    tables = ", ".join(
        f'"{table.schema}"."{table.name}"' if table.schema else f'"{table.name}"'
        for table in Base.metadata.tables.values()
    )
    async with engine.begin() as connection:
        await connection.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))


@pytest_asyncio.fixture
async def db_session(test_engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    await _truncate_all_tables(test_engine)
    session_factory = async_sessionmaker(test_engine, expire_on_commit=False)

    async with session_factory() as db:
        await seed_db(db)
        yield db


@pytest.fixture
def client(db_session: AsyncSession) -> Iterator[TestClient]:
    init_cache()
    yield TestClient(app)


@pytest.fixture(autouse=True)
def _no_external_side_effects(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _noop(*args, **kwargs):
        return None

    monkeypatch.setattr("app.dependencies.email_sender.EmailSender.send_email", _noop)


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        f"{API_PREFIX}/auth/login",
        data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['accessToken']}"}
