"""Integration tests run against a real, freshly migrated database. They run only with
INTEGRATION_TESTS set (see scripts/integration.sh); plain `pytest` skips them."""

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
    """Runs a coroutine on a fresh event loop; the pool and the Redis client are dropped after,
    as their connections belong to that loop."""
    from rounds.core.db import engine
    from rounds.integrations.redis import get_redis

    def run(coroutine):
        async def wrapped():
            try:
                return await coroutine
            finally:
                await engine.dispose()
                get_redis.cache_clear()

        return asyncio.run(wrapped())

    return run


@pytest.fixture(autouse=True)
def fresh_limits(monkeypatch):
    """The limits are read from Redis (database 15, see scripts/integration.sh) afresh in each
    test, not as an earlier test cached them."""
    from prepza_common.redis import memory_cache

    monkeypatch.setattr(memory_cache, "_entries", {})
