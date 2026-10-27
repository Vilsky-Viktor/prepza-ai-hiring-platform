import uuid
from datetime import UTC, datetime, timedelta

from prepza_common.config.constants import DELETED_USER

from app.constants.statuses import Status
from app.storage import accounts, generations


def test_deleting_a_user_keeps_company_tests_without_their_id(run):
    async def scenario():
        mine = await generations.create("gone", "company job", uuid.uuid4())
        other = await generations.create("stays", "someone else", uuid.uuid4())
        exported = await accounts.export("gone")

        await accounts.delete_user("gone")

        return exported, await generations.get(mine.id), await generations.get(other.id)

    exported, mine, other = run(scenario())

    assert [item["pasted_text"] for item in exported] == ["company job"]
    assert mine.owner_uid == DELETED_USER
    assert other.owner_uid == "stays"


def test_old_finished_generations_lose_their_pasted_text_only(run):
    async def scenario():
        finished = await generations.create("ann", "old finished text")
        await generations.update(finished.id, status=Status.DONE)
        running = await generations.create("ann", "still running")
        await generations.update(running.id, status=Status.RUNNING)

        count = await accounts.forget_texts(datetime.now(UTC) + timedelta(seconds=1), None)

        return count, await generations.get(finished.id), await generations.get(running.id)

    count, finished, running = run(scenario())

    assert count >= 1
    assert (finished.text, finished.status) == ("", Status.DONE)
    assert running.text == "still running"


def test_texts_are_blanked_a_batch_at_a_time_until_none_is_left(run, monkeypatch):
    monkeypatch.setattr(accounts, "DELETE_BATCH", 1)

    async def scenario():
        made = [await generations.create("ann", f"old text {n}") for n in range(3)]

        for generation in made:
            await generations.update(generation.id, status=Status.DONE)

        count = await accounts.forget_texts(datetime.now(UTC) + timedelta(seconds=1), None)

        return count, [(await generations.get(item.id)).text for item in made]

    count, texts = run(scenario())

    assert count >= 3
    assert texts == ["", "", ""]
