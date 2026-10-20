from unittest import mock

from prepza_common import db
from prepza_common.constants import (
    DB_POOL_RECYCLE_SECONDS,
    IDLE_IN_TRANSACTION_TIMEOUT,
    MIGRATION_LOCK_TIMEOUT,
)


def test_pooled_connections_are_replaced_by_age_not_pinged_on_every_use():
    with mock.patch.object(db, "create_async_engine") as create:
        db.database("postgresql+psycopg://user@/name", pool_size=2, max_overflow=1)

    options = create.call_args.kwargs
    assert options["pool_recycle"] == DB_POOL_RECYCLE_SECONDS
    assert "pool_pre_ping" not in options
    assert (options["pool_size"], options["max_overflow"]) == (2, 1)
    assert options["connect_args"] == {
        "options": f"-c idle_in_transaction_session_timeout={IDLE_IN_TRANSACTION_TIMEOUT}"
    }


def test_a_database_url_connects_through_psycopg():
    url = "postgresql://user:pass@db:5432/companies"

    assert db.sqlalchemy_url(url) == "postgresql+psycopg://user:pass@db:5432/companies"


def test_migrations_wait_only_so_long_for_a_lock():
    with mock.patch.object(db, "create_engine") as create:
        db.migration_engine("postgresql://user:pass@db:5432/companies")

    url = create.call_args.args[0]
    assert url == "postgresql+psycopg://user:pass@db:5432/companies"
    assert create.call_args.kwargs["connect_args"] == {
        "options": f"-c lock_timeout={MIGRATION_LOCK_TIMEOUT}"
    }


def test_old_rows_are_deleted_batch_after_batch_until_one_comes_up_short():
    import asyncio

    from sqlalchemy import Column, Integer
    from sqlalchemy.orm import declarative_base

    Row = declarative_base()

    class Old(Row):
        __tablename__ = "old"
        id = Column(Integer, primary_key=True)

    counts = iter([3, 3, 1])
    commits = []

    class FakeSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def execute(self, statement):
            return mock.Mock(rowcount=next(counts))

        async def commit(self):
            commits.append(True)

    deleted = asyncio.run(db.delete_in_batches(FakeSession, Old, Old.id < 10, batch=3))

    # Each batch is its own transaction; the short one is the last.
    assert deleted == 7
    assert len(commits) == 3
