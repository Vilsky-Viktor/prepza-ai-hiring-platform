import uuid

from rounds.repositories import practice_sessions
from rounds.services import sections
from tests.integration.factories import created, topic
from tests.integration.transactions import transaction


def test_only_the_latest_round_on_each_template_counts(run):
    user = f"talent-{uuid.uuid4()}"

    async def scenario():
        first, second = topic(), topic()
        # Another topic of the first template.
        more = first.model_copy(update={"id": uuid.uuid4()})
        # An older round on the first template, finished; then a newer one, half done.
        [old] = await created(user, uuid.uuid4(), [first], 60, practice=True)
        await transaction(sections.finish, old.id)
        done, _ = await created(user, uuid.uuid4(), [first, more], 60, practice=True)
        await transaction(sections.finish, done.id)
        # The second template: one round, untouched.
        await created(user, uuid.uuid4(), [second], 60, practice=True)
        # A company's interview isn't practice; someone else's practice isn't the talent's.
        await created(user, uuid.uuid4(), [second], 60, company_id=uuid.uuid4())
        await created(f"other-{user}", uuid.uuid4(), [first], 60, practice=True)
        found = await transaction(practice_sessions.latest_rounds, user)

        return (
            first.preparation_id,
            second.preparation_id,
            [(row.interview_set_id, row.status) for row in found],
        )

    first, second, found = run(scenario())

    assert sorted(found) == sorted(
        [(first, "finished"), (first, "in_progress"), (second, "in_progress")]
    )
