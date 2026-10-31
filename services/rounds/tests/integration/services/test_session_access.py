import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import update
from testee_common.auth.user import User

from rounds.constants.rounds import TIME_GRACE_SECONDS
from rounds.core.db import Session
from rounds.models.sessions import Session as SessionRow
from rounds.repositories import sessions
from rounds.services.session_access import get_own_session, get_owned_session
from tests.integration.factories import created, topic
from tests.integration.transactions import transaction

CANDIDATE = User(uid="cand", email="cand@example.com", email_verified=True)


def test_a_rating_after_the_deadline_doesnt_time_out_an_answer_still_in_its_grace(run):
    """The candidate picks in the question's last second: their rating or a page leave reaches
    the server first, a moment past the deadline. It must not record the question as timed out,
    so their answer, still within the grace, counts."""

    async def scenario():
        [row] = await created("cand", uuid.uuid4(), [topic()], 30, company_id=uuid.uuid4())
        await transaction(sessions.mark_shown, row.id)
        # Shown just over its 30 seconds ago, well within the grace.
        shown = datetime.now(UTC) - timedelta(seconds=31)

        async with Session() as session:
            await session.execute(
                update(SessionRow).where(SessionRow.id == row.id).values(question_shown_at=shown)
            )
            await session.commit()

        await get_own_session(row.id, CANDIDATE)
        after_rating = await transaction(sessions.get, row.id)
        await get_owned_session(row.id, CANDIDATE, TIME_GRACE_SECONDS)
        at_answer = await transaction(sessions.get, row.id)

        return after_rating, at_answer

    after_rating, at_answer = run(scenario())

    assert after_rating.answers == []
    # The answer's own check gives the grace: still nothing timed out.
    assert at_answer.answers == []


# Questions of very different lengths, so each gets a time of its own, none the average.
UNEVEN = [
    "Short?",
    "What does this print?\n\n```python\n"
    + "\n".join(f"total = total + item_{index}" for index in range(30))
    + "\n```",
]


def test_a_question_times_out_on_its_own_time_not_the_average(run):
    async def scenario():
        [row] = await created(
            "cand", uuid.uuid4(), [topic(texts=UNEVEN)], 60, company_id=uuid.uuid4()
        )
        own = row.questions[0]["seconds"]
        await transaction(sessions.mark_shown, row.id)
        # Shown just over its own time ago.
        shown = datetime.now(UTC) - timedelta(seconds=own + 1)

        async with Session() as session:
            await session.execute(
                update(SessionRow).where(SessionRow.id == row.id).values(question_shown_at=shown)
            )
            await session.commit()

        await get_owned_session(row.id, CANDIDATE)

        return row, own, await transaction(sessions.get, row.id)

    row, own, after = run(scenario())

    # The times differ and add up to the questions times the average.
    assert own != 60
    assert sum(question["seconds"] for question in row.questions) == 120
    assert [(answer.timed_out, answer.seconds) for answer in after.answers] == [(True, own)]
