import uuid

from alembic import command
from alembic.config import Config
from sqlalchemy import select, text

from rounds.core.db import Session
from rounds.helpers.practice import round_out
from rounds.models.answers import Answer
from rounds.models.outbox import OutboxEvent
from rounds.repositories import answer_counts, sessions
from rounds.services import invite_scores, sections
from tests.integration.factories import created, topic
from tests.integration.transactions import transaction


def ticked(row, index, right, seconds=20):
    """An answer ticking one right option of a multi-answer question (half its points), or one
    right and one wrong (none)."""
    question = row.questions[index]
    options = question["options"]
    picks = [next(i for i, option in enumerate(options) if option["correct"])]

    if not right:
        picks.append(next(i for i, option in enumerate(options) if not option["correct"]))

    return Answer(
        session_id=row.id,
        question_id=uuid.UUID(question["id"]),
        option_index=None,
        picks=sorted(picks),
        correct=False,
        score=50 if right else 0,
        seconds=seconds,
    )


def ran_out(row, index):
    return Answer(
        session_id=row.id,
        question_id=uuid.UUID(row.questions[index]["id"]),
        option_index=None,
        timed_out=True,
        correct=False,
        score=0,
        seconds=30,
    )


def test_multi_answer_answers_count_as_answered_not_as_timed_out(run):
    invite_id = uuid.uuid4()

    async def scenario():
        [row] = await created(
            "cand", invite_id, [topic(4, multi=True)], 30, company_id=uuid.uuid4()
        )
        await transaction(sessions.add_answer, ticked(row, 0, right=True, seconds=1))
        await transaction(sessions.add_answer, ticked(row, 1, right=False))
        await transaction(sessions.add_answer, ran_out(row, 2))
        saved = await transaction(sessions.get, row.id)
        totals = (await invite_scores.scores([invite_id]))[invite_id]
        counts = await transaction(answer_counts.for_sets, [row.interview_set_id])

        return saved, totals, counts[row.interview_set_id]

    saved, totals, counts = run(scenario())

    assert sorted(len(answer.picks or []) for answer in saved.answers) == [0, 1, 2]
    # Three of four shown: two ticked (one fast) and one ran out; half a point of three.
    assert (totals["progress"], totals["grade"]) == (75, 17)
    assert (totals["picked"], totals["fast_answers"]) == (2, 1)
    # Of the three answers, one timed out.
    assert counts == [1, 3]


def test_a_finished_section_tells_library_each_answers_credit(run):
    invite_id = uuid.uuid4()

    async def scenario():
        [row] = await created(
            "cand", invite_id, [topic(2, multi=True)], 30, company_id=uuid.uuid4()
        )
        await transaction(sessions.add_answer, ticked(row, 0, right=True))
        await transaction(sessions.add_answer, ran_out(row, 1))
        await transaction(sections.finish, row.id)

        async with Session() as session:
            events = await session.execute(
                select(OutboxEvent.event_type, OutboxEvent.data).where(
                    OutboxEvent.event_type.in_(["session.scored", "interview.finished"])
                )
            )

        ids = [question["id"] for question in row.questions]
        scored = next(
            data
            for kind, data in events.all()
            if kind == "session.scored" and data["answers"][0]["question_id"] in ids
        )
        finished = await session_finished(invite_id)

        return ids, scored, finished

    ids, scored, finished = run(scenario())
    results = {
        item["question_id"]: (item["credit"], item["timed_out"]) for item in scored["answers"]
    }

    assert results == {ids[0]: (0.5, False), ids[1]: (0.0, True)}
    # The one answer the candidate gave, not the one whose time ran out.
    assert finished["answered"] == 1


async def session_finished(invite_id):
    async with Session() as session:
        return await session.scalar(
            select(OutboxEvent.data).where(
                OutboxEvent.event_type == "interview.finished",
                OutboxEvent.data["candidate_invite_id"].astext == str(invite_id),
            )
        )


def test_a_practice_round_counts_ticked_answers_as_answered(run):
    async def scenario():
        round_id = uuid.uuid4()
        [row] = await created(
            f"talent-{round_id}", round_id, [topic(3, multi=True)], 60, practice=True
        )
        await transaction(sessions.add_answer, ticked(row, 0, right=True))
        await transaction(sessions.add_answer, ran_out(row, 1))

        return round_out(await transaction(sessions.list_for_invite, round_id), "Ledgers")

    found = run(scenario())

    assert (found.answered, found.total) == (1, 3)


def test_the_picks_migration_marks_answers_without_an_option_as_timed_out(run):
    async def setup():
        # A practice section: going down to 0023 takes sections' companies away, and an
        # interview section can't come back up without one (0030).
        [row] = await created("cand", uuid.uuid4(), [topic(2)], 30, practice=True)

        return row

    async def insert(row):
        async with Session() as session:
            for question, option in zip(row.questions, (0, None)):
                await session.execute(
                    text(
                        "INSERT INTO answers (id, session_id, question_id, option_index, correct, "
                        "score) VALUES (:id, :session_id, :question_id, :option, false, 0)"
                    ),
                    {
                        "id": uuid.uuid4(),
                        "session_id": row.id,
                        "question_id": uuid.UUID(question["id"]),
                        "option": option,
                    },
                )

            await session.commit()

    async def timed_out(row):
        async with Session() as session:
            found = await session.execute(
                select(Answer.question_id, Answer.timed_out, Answer.picks).where(
                    Answer.session_id == row.id
                )
            )

            return {str(question_id): (out, picks) for question_id, out, picks in found}

    row = run(setup())
    config = Config("alembic.ini")
    command.downgrade(config, "0023")
    run(insert(row))
    command.upgrade(config, "head")
    found = run(timed_out(row))

    assert found == {row.questions[0]["id"]: (False, None), row.questions[1]["id"]: (True, None)}
