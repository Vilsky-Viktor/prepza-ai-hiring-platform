import asyncio
from unittest import mock

import pytest
from prepza_common import db
from prepza_common.constants import (
    DB_POOL_RECYCLE_SECONDS,
    IDLE_IN_TRANSACTION_TIMEOUT,
    MIGRATION_LOCK_TIMEOUT,
    MIGRATION_STATEMENT_TIMEOUT,
    STATEMENT_TIMEOUT,
)
from sqlalchemy import Column, Integer
from sqlalchemy.orm import declarative_base

Row = declarative_base()


class Old(Row):
    __tablename__ = "old"
    id = Column(Integer, primary_key=True)
    flag = Column(Integer)


def fake_sessions(counts: list[int], commits: list):
    """A session factory whose statements report the next of `counts` rows, noting each
    commit in `commits`."""
    rowcounts = iter(counts)

    class FakeSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def execute(self, statement):
            return mock.Mock(rowcount=next(rowcounts))

        async def commit(self):
            commits.append(True)

    return FakeSession


def test_pooled_connections_are_replaced_by_age_not_pinged_on_every_use():
    with mock.patch.object(db, "create_async_engine") as create:
        db.database("postgresql+psycopg://user@/name", pool_size=2, max_overflow=1)

    options = create.call_args.kwargs
    assert options["pool_recycle"] == DB_POOL_RECYCLE_SECONDS
    assert "pool_pre_ping" not in options
    # A database error's text carries no query values (emails, names, answers).
    assert options["hide_parameters"] is True
    assert (options["pool_size"], options["max_overflow"]) == (2, 1)
    assert options["connect_args"] == {
        "options": f"-c idle_in_transaction_session_timeout={IDLE_IN_TRANSACTION_TIMEOUT} "
        f"-c statement_timeout={STATEMENT_TIMEOUT}"
    }


def test_a_database_url_connects_through_psycopg():
    url = "postgresql://user:pass@db:5432/companies"

    assert db.sqlalchemy_url(url) == "postgresql+psycopg://user:pass@db:5432/companies"


def test_migrations_wait_only_so_long_for_a_lock_and_run_only_so_long():
    with mock.patch.object(db, "create_engine") as create:
        db.migration_engine("postgresql://user:pass@db:5432/companies")

    url = create.call_args.args[0]
    assert url == "postgresql+psycopg://user:pass@db:5432/companies"
    assert create.call_args.kwargs["connect_args"] == {
        "options": f"-c lock_timeout={MIGRATION_LOCK_TIMEOUT} "
        f"-c statement_timeout={MIGRATION_STATEMENT_TIMEOUT}"
    }


@pytest.mark.parametrize(
    "run",
    [
        lambda sessions: db.delete_in_batches(sessions, Old, Old.id < 10),
        lambda sessions: db.update_in_batches(sessions, Old, {"flag": None}, Old.id < 10),
    ],
    ids=["delete", "update"],
)
def test_rows_go_batch_after_batch_until_one_comes_up_short(monkeypatch, run):
    monkeypatch.setattr(db, "DELETE_BATCH", 3)
    commits = []

    done = asyncio.run(run(fake_sessions([3, 3, 1], commits)))

    # Each batch is its own transaction; the short one is the last.
    assert done == 7
    assert len(commits) == 3


def test_a_deadline_stops_further_batches_and_the_next_run_goes_on(monkeypatch):
    monkeypatch.setattr(db, "DELETE_BATCH", 3)
    commits = []

    # The deadline has passed: the batch under way is the last.
    done = asyncio.run(db.delete_in_batches(fake_sessions([3, 3, 1], commits), Old, until=0))

    assert (done, len(commits)) == (3, 1)


def test_a_closed_set_becomes_a_check_condition_with_each_value_quoted():
    from enum import StrEnum

    class Status(StrEnum):
        OPEN = "open"
        SHUT = "it's shut"

    assert db.one_of("status", Status) == "status IN ('open', 'it''s shut')"
