import json
import uuid

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from testee_common.events import processed_events

from library.models.events import ProcessedEvent
from library.models.sets import Question

# Counts one answer: its credit (1 when right, 0 when wrong, a share of 1 for a multi-answer one
# partly right) and one pick for each option picked (:picks, {"option text": 1}). Only when the
# question still has the text that was answered: an answer to a question since re-generated
# belongs to its old content, not the new one. Returns how often the question has been shown:
# answered or timed out.
RECORD_ANSWER_SQL = text(
    """
    INSERT INTO question_stats (question_id, answers, correct, option_picks, updated_at)
    SELECT id, 1, CAST(:credit AS double precision), CAST(:picks AS jsonb), now()
    FROM questions
    WHERE id = :question_id AND text = :question_text
    ON CONFLICT (question_id) DO UPDATE SET
        answers = question_stats.answers + 1,
        correct = question_stats.correct + EXCLUDED.correct,
        option_picks = question_stats.option_picks || (
            SELECT coalesce(jsonb_object_agg(
                picked.key,
                coalesce((question_stats.option_picks ->> picked.key)::int, 0) + 1
            ), '{}'::jsonb)
            FROM jsonb_each(EXCLUDED.option_picks) AS picked
        ),
        updated_at = now()
    RETURNING answers + timeouts
    """
)

# Counts one candidate's result on a question: in the strong or weak group (or neither), and
# whether their time ran out. Only for the text that was answered, as above.
RECORD_RESULT_SQL = text(
    """
    INSERT INTO question_stats (
        question_id, answers, correct, option_picks, updated_at,
        strong_answers, strong_correct, weak_answers, weak_correct, timeouts
    )
    SELECT id, 0, 0, '{}'::jsonb, now(),
        CAST(:strong AS integer), CAST(:strong_correct AS double precision),
        CAST(:weak AS integer), CAST(:weak_correct AS double precision),
        CAST(:timed_out AS integer)
    FROM questions
    WHERE id = :question_id AND text = :question_text
    ON CONFLICT (question_id) DO UPDATE SET
        strong_answers = question_stats.strong_answers + EXCLUDED.strong_answers,
        strong_correct = question_stats.strong_correct + EXCLUDED.strong_correct,
        weak_answers = question_stats.weak_answers + EXCLUDED.weak_answers,
        weak_correct = question_stats.weak_correct + EXCLUDED.weak_correct,
        timeouts = question_stats.timeouts + EXCLUDED.timeouts,
        updated_at = now()
    """
)


def credit(result: dict) -> float:
    """An answer's credit from 0 to 1; events from before multi-answer questions have none."""
    return float(result.get("credit", 1.0 if result["correct"] else 0.0))


async def with_sources(
    session: AsyncSession, question_ids: list[uuid.UUID]
) -> dict[uuid.UUID, list[uuid.UUID]]:
    """Each question with the bank question it was copied from, if any: an original's answers
    add up across every test that uses it. One query for them all."""
    rows = await session.execute(
        select(Question.id, Question.source_question_id).where(Question.id.in_(question_ids))
    )
    sources = dict(rows.all())

    return {
        question_id: [question_id] + ([sources[question_id]] if sources.get(question_id) else [])
        for question_id in question_ids
    }


async def record_answer(
    session: AsyncSession,
    event_id: str,
    question_id: uuid.UUID,
    question_text: str,
    options: list[str],
    credit: float,
) -> dict[uuid.UUID, int] | None:
    """Counts one answer (the options picked, and its credit from 0 to 1) for the question and
    its bank original, in the caller's transaction and once per event. How often each counted
    question has now been shown, or None when the event was counted before. A question whose
    text has changed since isn't counted."""
    if not await processed_events.claim(session, ProcessedEvent, event_id):
        return None

    questions = (await with_sources(session, [question_id]))[question_id]
    shown = {}

    # Rows are always updated in the same order, so two events never wait on each other.
    for answered in sorted(questions):
        times = await session.scalar(
            RECORD_ANSWER_SQL,
            {
                "question_id": answered,
                "question_text": question_text,
                "picks": json.dumps(dict.fromkeys(options, 1)),
                "credit": credit,
            },
        )

        if times is not None:
            shown[answered] = times

    return shown


async def record_results(
    session: AsyncSession, event_id: str, group: str | None, results: list[dict]
) -> list[uuid.UUID] | None:
    """Counts one finished topic's results ({"question_id", "question_text", "correct",
    "credit", "timed_out"}; events from before multi-answer questions have no credit: 1 when
    correct) for each question and its bank original, in one transaction and once per
    event. `group` is the candidate's: strong, weak, or None in between (not counted there).
    The questions counted, or None when the event was counted before."""
    if not await processed_events.claim(session, ProcessedEvent, event_id):
        return None

    ids = [uuid.UUID(result["question_id"]) for result in results]
    sources = await with_sources(session, ids)
    # Rows are always updated in the same order, so two events never wait on each other.
    rows = sorted(
        (
            (answered, result)
            for question_id, result in zip(ids, results)
            for answered in sources[question_id]
        ),
        key=lambda row: row[0],
    )
    counted = []

    for answered, result in rows:
        await session.execute(
            RECORD_RESULT_SQL,
            {
                "question_id": answered,
                "question_text": result["question_text"],
                "strong": int(group == "strong"),
                "strong_correct": credit(result) if group == "strong" else 0.0,
                "weak": int(group == "weak"),
                "weak_correct": credit(result) if group == "weak" else 0.0,
                "timed_out": int(result["timed_out"]),
            },
        )
        counted.append(answered)

    return list(dict.fromkeys(counted))
