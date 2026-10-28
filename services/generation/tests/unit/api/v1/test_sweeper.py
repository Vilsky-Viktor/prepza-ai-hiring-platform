import asyncio
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.dialects import postgresql

from generation.constants.generation import (
    GENERATION_STOPPED,
    QUEUED_STUCK_AFTER_SECONDS,
    STUCK_AFTER_SECONDS,
)
from generation.repositories import generations
from generation.services import jobs, schedules


class FakeCheckpointer:
    def __init__(self):
        self.deleted = []

    async def adelete_thread(self, thread_id):
        self.deleted.append(thread_id)


def no_finished_threads(monkeypatch, threads=(), expired=()):
    async def fake_threads(session):
        return list(threads)

    async def fake_expire(session, before):
        return list(expired)

    monkeypatch.setattr(generations, "finished_threads", fake_threads)
    monkeypatch.setattr(generations, "expire_reviews", fake_expire)


def test_sweep_fails_generations_untouched_for_longer_than_a_job_may_run(monkeypatch):
    calls = []

    async def fake_fail_stuck(session, running_before, queued_before, error):
        calls.append((running_before, queued_before, error))

        return []

    monkeypatch.setattr(generations, "fail_stuck", fake_fail_stuck)
    no_finished_threads(monkeypatch)

    asyncio.run(schedules.sweep(FakeCheckpointer()))

    [(running_before, queued_before, error)] = calls
    now = datetime.now(UTC)
    assert (
        abs((running_before - (now - timedelta(seconds=STUCK_AFTER_SECONDS))).total_seconds()) < 5
    )
    # A queued one may only be waiting for a free worker, so it gets longer.
    queued_after = timedelta(seconds=QUEUED_STUCK_AFTER_SECONDS)
    assert abs((queued_before - (now - queued_after)).total_seconds()) < 5
    assert QUEUED_STUCK_AFTER_SECONDS > STUCK_AFTER_SECONDS
    assert error == GENERATION_STOPPED


def test_sweep_deletes_checkpoints_of_finished_generations(monkeypatch):
    async def fake_fail_stuck(session, running_before, queued_before, error):
        return []

    checkpointer = FakeCheckpointer()
    monkeypatch.setattr(generations, "fail_stuck", fake_fail_stuck)
    no_finished_threads(monkeypatch, ["done-1", "cancelled-1"])

    asyncio.run(schedules.sweep(checkpointer))

    assert checkpointer.deleted == ["done-1", "cancelled-1"]


def fake_session(statements, rowcount=0):
    """A session that records the statements a repository function runs."""

    class FakeSession:
        async def execute(self, statement):
            statements.append(statement)

            class Result:
                pass

            Result.rowcount = rowcount

            return Result()

        async def scalars(self, statement):
            statements.append(statement)

            return []

    return FakeSession()


def compiled(statement) -> str:
    return str(
        statement.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True})
    )


def test_only_queued_and_running_rows_are_swept(monkeypatch):
    statements = []
    session = fake_session(statements)

    asyncio.run(
        generations.fail_stuck(session, datetime.now(UTC), datetime.now(UTC), GENERATION_STOPPED)
    )

    sql = compiled(statements[0])
    assert "status = 'running' AND generations.updated_at <" in sql
    assert "status = 'queued' AND generations.updated_at <" in sql
    assert "'failed'" in sql


def test_only_done_and_cancelled_checkpoints_are_deleted(monkeypatch):
    statements = []
    asyncio.run(generations.finished_threads(fake_session(statements)))

    sql = compiled(statements[0])
    assert "IN ('done', 'cancelled')" in sql
    assert "failed" not in sql and "awaiting_review" not in sql
    # A run deletes a bounded batch; the next run takes the rest.
    assert "LIMIT 1000" in sql


def test_the_worker_runs_schedules_and_jobs_through_its_routes(monkeypatch):
    from fastapi.testclient import TestClient

    from generation.worker_main import app as worker_app

    called = []

    async def record(*args):
        called.append(args)

    for name in ("sweep", "key_check_batches", "retention"):
        monkeypatch.setattr(schedules, name, lambda *args, name=name: record(name))

    monkeypatch.setattr(jobs, "run_pipeline", record)
    worker_app.state.checkpointer = "checkpointer"
    worker_app.state.graph = "graph"
    client = TestClient(worker_app)

    for path in ("sweep", "key-check-batches", "retention"):
        assert client.post(f"/internal/schedules/{path}").status_code == 204

    assert called == [("sweep",), ("key_check_batches",), ("retention",)]


def test_worker_runs_only_a_generation_it_claims_from_the_queue(monkeypatch):
    """Failed by the sweeper, cancelled while it waited, or claimed by another delivery of the
    same job: it isn't queued any more, so this job doesn't run it."""
    started = []

    async def not_queued(session, _generation_id):
        return False

    async def run_pipeline(*args):
        started.append(args)

    monkeypatch.setattr(generations, "claim_run", not_queued)
    monkeypatch.setattr(jobs, "run_pipeline", run_pipeline)

    asyncio.run(jobs.run_generation(None, uuid.uuid4(), None))

    assert started == []


def test_claiming_a_run_moves_only_a_queued_generation(monkeypatch):
    statements = []
    session = fake_session(statements, rowcount=1)

    assert asyncio.run(generations.claim_run(session, uuid.uuid4())) is True

    sql = compiled(statements[0])
    assert "status='running'" in sql.replace(" ", "")
    assert "generations.status = 'queued'" in sql


def test_updates_never_touch_a_finished_generation(monkeypatch):
    statements = []
    session = fake_session(statements, rowcount=0)

    assert asyncio.run(generations.update(session, uuid.uuid4(), status="failed")) is False

    assert "NOT IN ('done', 'cancelled')" in compiled(statements[0])
