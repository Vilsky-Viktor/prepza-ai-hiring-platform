import uuid

from sqlalchemy import update

from app.models.answers import Answer
from app.models.sessions import Session
from app.storage import accounts, sessions
from app.storage.db import Session as Db
from tests.integration.factories import option_index, topic


def test_deleting_a_user_removes_their_interview_sessions(run):
    async def scenario():
        [session] = await sessions.create_many(
            "gone", uuid.uuid4(), [topic()], 60, company_id=uuid.uuid4()
        )
        question = session.questions[0]
        await sessions.add_answer(
            Answer(
                session_id=session.id,
                question_id=uuid.UUID(question["id"]),
                option_index=option_index(question, True),
                correct=True,
                score=100,
            ),
            ("answer.recorded", {"question_id": question["id"]}),
        )
        [kept] = await sessions.create_many(
            "stays", uuid.uuid4(), [topic()], 60, company_id=uuid.uuid4()
        )

        async with Db() as db:
            await db.execute(update(Session).where(Session.id == session.id).values(final_score=50))
            await db.commit()

        exported = await accounts.export("gone")

        await accounts.delete_user("gone")
        # Safe to repeat: a retried deletion finds nothing left.
        await accounts.delete_user("gone")

        return exported, await sessions.get(session.id), await sessions.get(kept.id)

    exported, session, kept = run(scenario())

    [section] = exported["interview_sections"]
    [answer] = section["answers"]

    assert answer["your_answer"] == "right"
    # Whether a company interview's answer was right isn't the candidate's to see; their grade
    # is.
    assert "correct" not in answer
    assert section["final_score"] == 50
    assert session is None
    assert kept is not None
