import uuid
from datetime import UTC, datetime, timedelta

from prepza_common.auth.user import User
from sqlalchemy import update

from app.constants.rounds import TIME_GRACE_SECONDS
from app.models.sessions import Session as SessionRow
from app.services.session_access import get_own_session, get_owned_session
from app.storage import sessions
from app.storage.db import Session
from tests.integration.factories import topic

CANDIDATE = User(uid="cand", email="cand@example.com", email_verified=True)


def test_a_rating_after_the_deadline_doesnt_time_out_an_answer_still_in_its_grace(run):
    """The candidate picks in the question's last second: their rating or a page leave reaches
    the server first, a moment past the deadline. It must not record the question as timed out,
    so their answer, still within the grace, counts."""

    async def scenario():
        [row] = await sessions.create_many(
            "cand", uuid.uuid4(), [topic()], 30, company_id=uuid.uuid4()
        )
        await sessions.mark_shown(row.id)
        # Shown just over its 30 seconds ago, well within the grace.
        shown = datetime.now(UTC) - timedelta(seconds=31)

        async with Session() as session:
            await session.execute(
                update(SessionRow).where(SessionRow.id == row.id).values(question_shown_at=shown)
            )
            await session.commit()

        await get_own_session(row.id, CANDIDATE)
        after_rating = await sessions.get(row.id)
        await get_owned_session(row.id, CANDIDATE, TIME_GRACE_SECONDS)
        at_answer = await sessions.get(row.id)

        return after_rating, at_answer

    after_rating, at_answer = run(scenario())

    assert after_rating.answers == []
    # The answer's own check gives the grace: still nothing timed out.
    assert at_answer.answers == []
