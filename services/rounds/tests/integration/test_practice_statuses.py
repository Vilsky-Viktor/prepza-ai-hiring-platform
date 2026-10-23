import uuid

from app.storage import practice_sessions, sessions
from tests.integration.factories import topic


def test_only_the_latest_round_on_each_template_counts(run):
    user = f"talent-{uuid.uuid4()}"

    async def scenario():
        first, second = topic(), topic()
        # Another topic of the first template.
        more = first.model_copy(update={"id": uuid.uuid4()})
        # An older round on the first template, finished; then a newer one, half done.
        [old] = await sessions.create_many(user, uuid.uuid4(), [first], 60, practice=True)
        await sessions.finish(old.id)
        done, _ = await sessions.create_many(user, uuid.uuid4(), [first, more], 60, practice=True)
        await sessions.finish(done.id)
        # The second template: one round, untouched.
        await sessions.create_many(user, uuid.uuid4(), [second], 60, practice=True)
        # A company's interview isn't practice; someone else's practice isn't the talent's.
        await sessions.create_many(user, uuid.uuid4(), [second], 60, company_id=uuid.uuid4())
        await sessions.create_many(f"other-{user}", uuid.uuid4(), [first], 60, practice=True)
        found = await practice_sessions.latest_round_sections(user)

        return first.preparation_id, second.preparation_id, found

    first, second, found = run(scenario())

    assert sorted(found) == sorted(
        [(first, "finished"), (first, "in_progress"), (second, "in_progress")]
    )
