import uuid
from datetime import UTC, datetime, timedelta

from prepza_common.config.constants import DELETED_USER

from generation.constants.statuses import Status
from generation.repositories import accounts, generations
from generation.services import schedules
from tests.integration.transactions import transaction


def test_deleting_a_user_keeps_company_tests_without_their_id(run):
    async def scenario():
        mine = await transaction(generations.create, "gone", "company job", uuid.uuid4())
        other = await transaction(generations.create, "stays", "someone else", uuid.uuid4())
        exported = await transaction(accounts.export, "gone")

        await transaction(accounts.delete_user, "gone")

        return (
            exported,
            await transaction(generations.get, mine.id),
            await transaction(generations.get, other.id),
        )

    exported, mine, other = run(scenario())

    assert [item["pasted_text"] for item in exported] == ["company job"]
    assert mine.owner_uid == DELETED_USER
    assert other.owner_uid == "stays"


def test_old_finished_generations_lose_their_pasted_text_only(run):
    async def scenario():
        finished = await transaction(generations.create, "ann", "old finished text")
        await transaction(generations.update, finished.id, status=Status.DONE)
        running = await transaction(generations.create, "ann", "still running")
        await transaction(generations.update, running.id, status=Status.RUNNING)

        count = await schedules.forget_texts(datetime.now(UTC) + timedelta(seconds=1), None)

        return (
            count,
            await transaction(generations.get, finished.id),
            await transaction(generations.get, running.id),
        )

    count, finished, running = run(scenario())

    assert count >= 1
    assert (finished.text, finished.status) == ("", Status.DONE)
    assert running.text == "still running"


def test_texts_are_blanked_a_batch_at_a_time_until_none_is_left(run, monkeypatch):
    monkeypatch.setattr(accounts, "DELETE_BATCH", 1)
    monkeypatch.setattr(schedules, "DELETE_BATCH", 1)

    async def scenario():
        made = [await transaction(generations.create, "ann", f"old text {n}") for n in range(3)]

        for generation in made:
            await transaction(generations.update, generation.id, status=Status.DONE)

        count = await schedules.forget_texts(datetime.now(UTC) + timedelta(seconds=1), None)

        return count, [(await transaction(generations.get, item.id)).text for item in made]

    count, texts = run(scenario())

    assert count >= 3
    assert texts == ["", "", ""]
