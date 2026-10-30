import uuid
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from library.constants.quality import MIN_ANSWERS
from library.constants.sets import SetKind

# The company's set is kept out of the bank by its interview's opt-out (interview_privacy, by
# the set's id or the generation that saved it).
PRIVATE = """EXISTS (
    SELECT FROM interview_privacy p
    WHERE p.keep_private AND p.company_id = s.company_id
        AND (p.set_id = s.id OR p.generation_id = s.generation_id)
)"""
# A company's own question: generated for its interview, not a copy of a template's or of a bank
# question.
OWN = "s.kind = :interview AND q.source_question_id IS NULL AND q.bank_question_id IS NULL"
REPORTED = "EXISTS (SELECT FROM question_reports r WHERE r.question_id = {question}.id)"

# What the filter hasn't checked as it reads now: proven questions, which may join, and flagged
# ones, which only get a verdict (export_flagged.py's eval traps).
CANDIDATES_SQL = text(
    f"""
    SELECT q.id, t.title, q.text, q.options
    FROM question_stats qs
    JOIN questions q ON q.id = qs.question_id
    JOIN topics t ON t.id = q.topic_id
    JOIN sets s ON s.id = t.set_id
    LEFT JOIN bank_checks bc ON bc.question_id = q.id
    WHERE qs.company_id IS NOT NULL AND (qs.answers >= :min_answers OR qs.flag IS NOT NULL)
        AND {OWN} AND NOT {PRIVATE}
        AND (bc.question_id IS NULL OR bc.text_hash <> md5(q.text))
        AND (CAST(:after AS uuid) IS NULL OR q.id > CAST(:after AS uuid))
    ORDER BY q.id
    LIMIT :limit
    """
)

SAVE_CHECKS_SQL = text(
    """
    INSERT INTO bank_checks (question_id, text_hash, passed)
    SELECT id, md5(:text), :passed FROM questions WHERE id = :question_id
    ON CONFLICT (question_id) DO UPDATE
        SET text_hash = excluded.text_hash, passed = excluded.passed, checked_at = now()
    """
)

# Copies the proven questions that passed the filter, as they read when checked, into the bank
# with their topic's embedding and without their company. `{which}` picks the questions.
JOIN_SQL = f"""
    INSERT INTO bank_questions
        (id, source_question_id, text, options, level, language, embedding)
    SELECT gen_random_uuid(), q.id, q.text, q.options, s.level, s.language, t.embedding
    FROM questions q
    JOIN topics t ON t.id = q.topic_id
    JOIN sets s ON s.id = t.set_id
    JOIN question_stats qs ON qs.question_id = q.id
    JOIN bank_checks bc ON bc.question_id = q.id
    WHERE {{which}} AND {OWN} AND NOT {PRIVATE}
        AND bc.passed AND NOT bc.barred AND bc.text_hash = md5(q.text)
        AND qs.answers >= :min_answers AND qs.flag IS NULL
        AND t.embedding IS NOT NULL
        AND NOT {REPORTED.format(question="q")}
        AND NOT EXISTS (SELECT FROM question_revisions v WHERE v.question_id = q.id)
    ON CONFLICT (source_question_id) DO NOTHING
"""
JOIN_QUESTIONS_SQL = text(JOIN_SQL.format(which="q.id = ANY(:ids)"))
NAMED_SET = "s.company_id = :company_id AND (s.id = :set_id OR s.generation_id = :generation_id)"
JOIN_SET_SQL = text(JOIN_SQL.format(which=NAMED_SET))

LEAVE_SET_SQL = text(
    f"""
    DELETE FROM bank_questions b
    USING questions q, topics t, sets s
    WHERE b.source_question_id = q.id AND t.id = q.topic_id AND s.id = t.set_id AND {NAMED_SET}
    """
)

# The bank copies of these questions, and those these questions are copies of.
LEAVE_SQL = text(
    """
    DELETE FROM bank_questions
    WHERE source_question_id = ANY(:ids)
        OR id IN (SELECT bank_question_id FROM questions WHERE id = ANY(:ids))
    RETURNING source_question_id
    """
)
BAR_SQL = text("UPDATE bank_checks SET barred = true WHERE question_id = ANY(:ids)")

# Bank copies whose source or a copy was flagged or reported, or whose source's interview was
# kept private, since they joined: a check made in a transaction that raced their joining missed
# them. `private` says no flag or report is why.
STALE_SQL = text(
    f"""
    SELECT b.id, b.source_question_id, NOT (qs.flag IS NOT NULL OR {REPORTED.format(question="q")})
    FROM bank_questions b
    JOIN questions q ON q.id = b.source_question_id
    JOIN topics t ON t.id = q.topic_id
    JOIN sets s ON s.id = t.set_id
    LEFT JOIN question_stats qs ON qs.question_id = q.id
    WHERE qs.flag IS NOT NULL OR {REPORTED.format(question="q")} OR {PRIVATE}
    UNION
    SELECT b.id, b.source_question_id, false
    FROM bank_questions b
    JOIN questions c ON c.bank_question_id = b.id
    LEFT JOIN question_stats cs ON cs.question_id = c.id
    WHERE cs.flag IS NOT NULL OR {REPORTED.format(question="c")}
    LIMIT :limit
    """
)

SET_PRIVACY_SQL = text(
    """
    INSERT INTO interview_privacy
        (interview_id, company_id, set_id, generation_id, keep_private, changed_at)
    VALUES (:interview_id, :company_id, :set_id, :generation_id, :keep_private, :changed_at)
    ON CONFLICT (interview_id) DO UPDATE
        SET keep_private = excluded.keep_private, changed_at = excluded.changed_at,
            set_id = coalesce(excluded.set_id, interview_privacy.set_id),
            generation_id = coalesce(excluded.generation_id, interview_privacy.generation_id)
        WHERE interview_privacy.changed_at < excluded.changed_at
            AND interview_privacy.company_id = excluded.company_id
    RETURNING interview_id
    """
)
FORGET_INTERVIEW_SQL = text(
    "DELETE FROM interview_privacy WHERE interview_id = :interview_id AND company_id = :company_id"
)

PARAMS = {"interview": SetKind.INTERVIEW, "min_answers": MIN_ANSWERS}


async def candidates(
    session: AsyncSession, limit: int, after: uuid.UUID | None
) -> list[tuple[uuid.UUID, str, str, list]]:
    """Companies' questions for the filter: (id, topic, text, options), in id order."""
    params = PARAMS | {"limit": limit, "after": after}

    return [tuple(row) for row in await session.execute(CANDIDATES_SQL, params)]


async def save_checks(session: AsyncSession, checks: list[tuple[uuid.UUID, str, bool]]) -> None:
    """Each verdict for the wording it was given on; a question gone meanwhile is skipped."""
    rows = [{"question_id": q, "text": wording, "passed": passed} for q, wording, passed in checks]

    if rows:
        await session.execute(SAVE_CHECKS_SQL, rows)


async def join(session: AsyncSession, question_ids: list[uuid.UUID]) -> None:
    await session.execute(JOIN_QUESTIONS_SQL, PARAMS | {"ids": question_ids})


def named(company_id: uuid.UUID, set_id, generation_id) -> dict:
    return {"company_id": company_id, "set_id": set_id, "generation_id": generation_id}


async def join_set(session: AsyncSession, company_id: uuid.UUID, set_id, generation_id) -> None:
    """The set's questions that may join, after its interview's opt-out was taken back."""
    await session.execute(JOIN_SET_SQL, PARAMS | named(company_id, set_id, generation_id))


async def leave_set(session: AsyncSession, company_id: uuid.UUID, set_id, generation_id) -> None:
    """The set's questions out of the bank; copies already reused elsewhere stay."""
    await session.execute(LEAVE_SET_SQL, named(company_id, set_id, generation_id))


async def leave(session: AsyncSession, question_ids: list[uuid.UUID]) -> None:
    """Flagged or reported questions out of the bank, with the bank questions they're copies of,
    for everyone; their sources never join again."""
    gone = await session.scalars(LEAVE_SQL, {"ids": question_ids})
    await bar(session, [source for source in gone if source is not None])


async def bar(session: AsyncSession, question_ids: list[uuid.UUID]) -> None:
    if question_ids:
        await session.execute(BAR_SQL, {"ids": question_ids})


async def stale(session: AsyncSession, limit: int) -> list[tuple[uuid.UUID, uuid.UUID, bool]]:
    """(bank id, source id, only kept private) of bank copies that should have left."""
    return [tuple(row) for row in await session.execute(STALE_SQL, PARAMS | {"limit": limit})]


async def remove(session: AsyncSession, bank_ids: list[uuid.UUID]) -> None:
    await session.execute(
        text("DELETE FROM bank_questions WHERE id = ANY(:ids)"), {"ids": bank_ids}
    )


async def set_privacy(
    session: AsyncSession,
    interview_id: uuid.UUID,
    company_id: uuid.UUID,
    set_id,
    generation_id,
    keep_private: bool,
    changed_at: datetime,
) -> bool:
    """The interview's opt-out, unless a newer change came first. Whether it was saved."""
    saved = await session.scalar(
        SET_PRIVACY_SQL,
        named(company_id, set_id, generation_id)
        | {"interview_id": interview_id, "keep_private": keep_private, "changed_at": changed_at},
    )

    return saved is not None


async def forget_interview(session: AsyncSession, interview_id, company_id) -> None:
    await session.execute(
        FORGET_INTERVIEW_SQL, {"interview_id": interview_id, "company_id": company_id}
    )


async def forget_company(session: AsyncSession, company_id) -> None:
    """A deleted company's opt-outs: one row per interview, few enough for one statement."""
    await session.execute(
        text("DELETE FROM interview_privacy WHERE company_id = :company_id"),
        {"company_id": company_id},
    )


async def bank_ids(session: AsyncSession, ids: list[uuid.UUID]) -> set[uuid.UUID]:
    """Which of `ids` are bank questions (a new interview's reused ones)."""
    if not ids:
        return set()

    found = await session.scalars(
        text("SELECT id FROM bank_questions WHERE id = ANY(:ids)"), {"ids": ids}
    )

    return set(found)
