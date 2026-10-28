import uuid

from sqlalchemy import update

from rounds.core.db import Session as Db
from rounds.models.answers import Answer
from rounds.models.sessions import Session
from rounds.repositories import accounts, sessions
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


def test_candidates_and_learners_are_listed_apart_a_page_at_a_time(run):
    """A candidate took a company's interview (a member's own try, a preview, doesn't count);
    a learner took a free practice round. Each once, in order, after the last page's last id."""
    tag = uuid.uuid4().hex[:8]
    cat, cy, lea, member = (f"{tag}-{name}" for name in ("a-cat", "b-cy", "c-lea", "d-member"))

    async def scenario():
        for user_id in (cat, cy):
            for _ in range(2):
                await sessions.create_many(
                    user_id, uuid.uuid4(), [topic()], 60, company_id=uuid.uuid4()
                )

        await sessions.create_many(lea, uuid.uuid4(), [topic()], 60, practice=True)
        await sessions.create_many(
            member, uuid.uuid4(), [topic()], 60, preview=True, company_id=uuid.uuid4()
        )
        candidates = await accounts.user_ids(False, f"{tag}-", 1)
        more = await accounts.user_ids(False, candidates[-1], 1)
        learners = await accounts.user_ids(True, f"{tag}-", 1000)

        return candidates, more, [user for user in learners if user.startswith(tag)]

    candidates, more, learners = run(scenario())

    assert (candidates, more) == ([cat], [cy])
    assert learners == [lea]
