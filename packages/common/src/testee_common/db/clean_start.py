"""Integration tests' clean start (services' tests/integration): before each test, the tables a
fresh migration left empty are emptied again, the tests' own Redis database is flushed and the
shared HTTP client is dropped (it belongs to an earlier test's event loop), so no test meets
another's rows, keys or connections. Rows the migrations seed stay. It only ever touches a
"<service>_test" database and Redis database 15 (scripts/integration.sh), never dev data."""

from redis import Redis
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from testee_common.http import http

TEST_REDIS_DATABASE = "15"


def _engine(database_url: str):
    url = make_url(database_url)

    if not (url.database or "").endswith("_test"):
        raise RuntimeError(f"not a test database: {url.database}")

    return create_engine(url.set(drivername="postgresql+psycopg"))


def tables_left_empty(database_url: str) -> list[str]:
    """The tables with no rows in a freshly migrated database: those the tests fill."""
    engine = _engine(database_url)

    with engine.connect() as connection:
        tables = connection.execute(
            text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        ).scalars()
        empty = [
            table
            for table in tables
            if not connection.execute(text(f'SELECT EXISTS (SELECT FROM "{table}")')).scalar()
        ]

    engine.dispose()

    return empty


def start_clean(database_url: str, tables: list[str], redis_url: str) -> None:
    """Empties `tables` (from tables_left_empty) and the tests' Redis database, and drops the
    shared HTTP client."""
    if not redis_url.rstrip("/").endswith(f"/{TEST_REDIS_DATABASE}"):
        raise RuntimeError("not the tests' Redis database")

    engine = _engine(database_url)

    if tables:
        with engine.begin() as connection:
            # Work an earlier test left running (a transaction still open) is ended first: it
            # would deadlock with the truncate, and a test starts clean of it anyway.
            connection.execute(
                text(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity"
                    " WHERE datname = current_database() AND pid <> pg_backend_pid()"
                    " AND state <> 'idle'"
                )
            )
            names = ", ".join(f'"{table}"' for table in tables)
            connection.execute(text(f"TRUNCATE {names} RESTART IDENTITY"))

    engine.dispose()

    with Redis.from_url(redis_url) as redis:
        redis.flushdb()

    http.get_client.cache_clear()
