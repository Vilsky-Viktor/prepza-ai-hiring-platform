"""Integration tests run against a real, freshly migrated database and a real Redis. They run
only with INTEGRATION_TESTS set (see scripts/integration.sh); plain `pytest` skips them."""

import asyncio
import os

import pytest
from alembic import command
from alembic.config import Config
from prepza_common.db.clean_start import start_clean, tables_left_empty
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

if not os.getenv("INTEGRATION_TESTS"):
    collect_ignore_glob = ["test_*.py", "*/test_*.py"]


@pytest.fixture(scope="session", autouse=True)
def database():
    """Creates the test database from scratch, runs every migration, and drops it afterwards;
    gives the tables the migrations left empty, those the tests fill."""
    url = make_url(os.environ["DATABASE_URL"])
    admin = create_engine(
        url.set(drivername="postgresql+psycopg", database="postgres"),
        isolation_level="AUTOCOMMIT",
    )

    with admin.connect() as connection:
        connection.execute(text(f'DROP DATABASE IF EXISTS "{url.database}" WITH (FORCE)'))
        connection.execute(text(f'CREATE DATABASE "{url.database}"'))

    command.upgrade(Config("alembic.ini"), "head")

    yield tables_left_empty(os.environ["DATABASE_URL"])

    with admin.connect() as connection:
        connection.execute(text(f'DROP DATABASE IF EXISTS "{url.database}" WITH (FORCE)'))

    admin.dispose()


@pytest.fixture(autouse=True)
def clean_start(database):
    """Every test starts clean: the tables the tests fill emptied and the tests' Redis database
    flushed, whatever an earlier test left."""
    start_clean(os.environ["DATABASE_URL"], database, os.environ["REDIS_URL"])


@pytest.fixture
def run():
    """Runs a coroutine on a fresh event loop; the database pool and the Redis client are
    closed after, as their connections belong to that loop."""
    from notifications.core.db import engine
    from notifications.integrations.redis import get_redis

    def run(coroutine):
        async def wrapped():
            try:
                return await coroutine
            finally:
                await engine.dispose()
                await get_redis().aclose()
                get_redis.cache_clear()

        return asyncio.run(wrapped())

    return run


@pytest.fixture(autouse=True)
def locally(monkeypatch):
    """A demo- project: Pub/Sub's pushes aren't token-checked, as with the emulator."""
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "demo-test")


@pytest.fixture
def teams(monkeypatch):
    """Each company's members by id ({company id: [user ids]}), as companies would answer."""
    found = {}

    async def members(company_ids):
        return [
            {"id": cid, "name": "Acme", "members": [{"user_id": u, "editor": False} for u in ids]}
            for cid, ids in found.items()
            if cid in company_ids
        ]

    async def company_ids(user_id):
        return [cid for cid, ids in found.items() if user_id in ids]

    async def account_created(user_id):
        return None

    from notifications.integrations import accounts, companies

    monkeypatch.setattr(companies, "members", members)
    monkeypatch.setattr(companies, "company_ids", company_ids)
    monkeypatch.setattr(accounts, "account_created", account_created)

    return found
