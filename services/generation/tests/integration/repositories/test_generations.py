import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from generation.constants.statuses import Status
from generation.repositories import generations
from tests.integration.transactions import transaction


def test_a_saved_generation_reads_back(run):
    async def scenario():
        created = await transaction(generations.create, "ann", "Senior Python developer")

        return await transaction(generations.get, created.id)

    found = run(scenario())

    assert (found.owner_uid, found.text, found.status) == (
        "ann",
        "Senior Python developer",
        Status.QUEUED,
    )


def test_running_generations_untouched_for_long_and_queued_ones_waiting_longer_are_failed(run):
    async def scenario():
        now = datetime.now(UTC)
        running = await transaction(generations.create, "ann", "running")
        await transaction(generations.claim_run, running.id)
        queued = await transaction(generations.create, "ann", "queued")
        done = await transaction(generations.create, "ann", "done")
        await transaction(generations.update, done.id, status=Status.DONE)
        # Untouched since a moment ago: long enough for a running one, not for a queued one.
        first = await transaction(
            generations.fail_stuck, now + timedelta(seconds=1), now, "stopped"
        )
        second = await transaction(
            generations.fail_stuck,
            now + timedelta(seconds=1),
            now + timedelta(seconds=1),
            "stopped",
        )
        # Nothing new has stalled since, so another sweep changes nothing.
        again = await transaction(generations.fail_stuck, now - timedelta(hours=1), now, "stopped")

        return (
            [row.id for row in first],
            [row.id for row in second],
            again,
            running.id,
            queued.id,
            await transaction(generations.get, running.id),
            await transaction(generations.get, done.id),
        )

    first, second, again, running_id, queued_id, running, done = run(scenario())

    # Other tests' generations share the database; these are among those failed.
    assert running_id in first and queued_id not in first
    assert queued_id in second
    assert again == []
    assert (running.status, running.error) == (Status.FAILED, "stopped")
    assert done.status == Status.DONE


def test_a_queued_generation_is_claimed_once_and_finished_ones_never_change(run):
    async def scenario():
        generation = await transaction(generations.create, "ann", "claimed")
        claims = [await transaction(generations.claim_run, generation.id) for _ in range(2)]
        await transaction(generations.update, generation.id, status=Status.DONE)
        failed = await transaction(
            generations.update, generation.id, status=Status.FAILED, error="late"
        )

        return claims, failed, await transaction(generations.get, generation.id)

    claims, failed, generation = run(scenario())

    assert claims == [True, False]
    assert failed is False
    assert (generation.status, generation.error) == (Status.DONE, None)


def test_generations_are_found_by_their_ids(run):
    async def scenario():
        created = await transaction(generations.create, "ann", "by ids")

        return created.id, await transaction(generations.by_ids, [created.id, uuid.uuid4()])

    created, found = run(scenario())

    assert [row.id for row in found] == [created]


def test_a_sweep_fails_at_most_a_batch_and_the_next_takes_the_rest(run, monkeypatch):
    monkeypatch.setattr(generations, "SWEEP_BATCH", 1)

    async def scenario():
        now = datetime.now(UTC)
        made = [
            await transaction(generations.create, "ann", f"queued {index}") for index in range(2)
        ]
        ours = {row.id for row in made}
        sweeps = []

        # Other tests' generations may be stuck too: sweep until ours are both failed.
        while ours - {row.id for sweep in sweeps for row in sweep}:
            sweeps.append(
                await transaction(
                    generations.fail_stuck, now, now + timedelta(seconds=1), "stopped"
                )
            )

        return sweeps

    sweeps = run(scenario())

    assert all(len(sweep) == 1 for sweep in sweeps)


def test_a_template_takes_one_queued_addition_at_a_time(run):
    template_id = uuid.uuid4()

    async def scenario():
        first = await transaction(generations.create_addition, "ann", template_id, "en", None)

        with pytest.raises(IntegrityError):
            await transaction(generations.create_addition, "ann", template_id, "en", 30)

        latest = await transaction(generations.latest_addition, template_id)

        return first, latest

    first, latest = run(scenario())

    assert latest.id == first.id
    assert (latest.status, latest.question_count) == (Status.QUEUED, None)
