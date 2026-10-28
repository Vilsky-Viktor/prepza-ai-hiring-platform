import uuid
from datetime import UTC, datetime

from prepza_common.db.db import delete_in_batches
from prepza_common.events import outbox
from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from rounds.constants.integrity import (
    FAST_ANSWER_SECONDS,
    MIN_TAB_LEAVE_SECONDS,
    IntegritySignal,
)
from rounds.constants.rounds import SESSION_DELETE_BATCH, RoundStatus
from rounds.models.answers import Answer
from rounds.models.outbox import OutboxEvent
from rounds.models.sessions import Session as RoundSession
from rounds.models.signals import Signal

# Signals are read only for a scorecard (list_for_invite's `signals`).
LOAD_SESSION = [selectinload(RoundSession.answers)]


async def add_all(session: AsyncSession, rows: list[RoundSession]) -> None:
    """Saves new sections; a second start for the same invite fails on its unique constraint
    here, at the flush, rather than at the commit."""
    session.add_all(rows)
    await session.flush()


async def get(session: AsyncSession, session_id: uuid.UUID) -> RoundSession | None:
    return await session.get(RoundSession, session_id, options=LOAD_SESSION)


async def list_for_invite(
    session: AsyncSession, candidate_invite_id: uuid.UUID, signals: bool = False
) -> list[RoundSession]:
    query = (
        select(RoundSession)
        .where(RoundSession.candidate_invite_id == candidate_invite_id)
        .options(*LOAD_SESSION, *([selectinload(RoundSession.signals)] if signals else []))
        .order_by(RoundSession.started_at, RoundSession.id)
    )

    return list(await session.scalars(query))


async def invite_counts(
    session: AsyncSession, invite_ids: list[uuid.UUID]
) -> dict[uuid.UUID, dict]:
    """Each candidate's questions, whether every section finished, their answers (all, their
    score's sum, the fast ones and the picked ones, not timed out) and their integrity signals,
    counted in the database rather than from every session's questions and answers."""
    invite = RoundSession.candidate_invite_id
    chosen = invite.in_(invite_ids)
    sections_query = (
        select(
            invite,
            func.sum(func.jsonb_array_length(RoundSession.questions)),
            func.bool_and(RoundSession.status == RoundStatus.FINISHED),
        )
        .where(chosen)
        .group_by(invite)
    )
    answers_query = (
        select(
            invite,
            func.count(Answer.id),
            func.sum(Answer.score),
            func.count(Answer.id).filter(~Answer.timed_out, Answer.seconds < FAST_ANSWER_SECONDS),
            func.count(Answer.id).filter(~Answer.timed_out),
        )
        .join(Answer, Answer.session_id == RoundSession.id)
        .where(chosen)
        .group_by(invite)
    )
    signals_query = (
        select(
            invite,
            func.count(Signal.id).filter(
                Signal.kind == IntegritySignal.TAB_LEAVE,
                or_(
                    Signal.away_seconds.is_(None),
                    Signal.away_seconds >= MIN_TAB_LEAVE_SECONDS,
                ),
            ),
            func.count(Signal.id).filter(Signal.kind == IntegritySignal.COPY),
        )
        .join(Signal, Signal.session_id == RoundSession.id)
        .where(chosen)
        .group_by(invite)
    )
    sections = (await session.execute(sections_query)).all()
    answers = {row[0]: row[1:] for row in await session.execute(answers_query)}
    signals = {row[0]: row[1:] for row in await session.execute(signals_query)}
    counts = {}

    for invite_id, total, finished in sections:
        answered, score_sum, fast_answers, picked = answers.get(invite_id, (0, 0, 0, 0))
        tab_leaves, copies = signals.get(invite_id, (0, 0))
        counts[invite_id] = {
            "total": total,
            "finished": finished,
            "answered": answered,
            "score_sum": score_sum or 0,
            "fast_answers": fast_answers,
            "picked": picked,
            "tab_leaves": tab_leaves,
            "copies": copies,
        }

    return counts


async def mark_shown(session: AsyncSession, session_id: uuid.UUID) -> datetime:
    """Starts the clock on the waiting question and returns when it started; reloading the
    page, or a second tab asking at the same moment, gets the same time."""
    return await session.scalar(
        update(RoundSession)
        .where(RoundSession.id == session_id)
        .values(question_shown_at=func.coalesce(RoundSession.question_shown_at, datetime.now(UTC)))
        .returning(RoundSession.question_shown_at)
    )


async def add_answer(
    session: AsyncSession, answer: Answer, event: tuple[str, dict] | None = None
) -> bool:
    """Saves the answer (and its event, when it has one) and stops the clock, so the next
    question starts its own. A question that timed out has no event: nothing was picked.

    False when the section is no longer running. A question that already has an answer (two
    requests timing out the same question at once) fails on its unique constraint at the
    flush: the caller's transaction is then over.
    """
    # Stopping the clock locks the section, so it can't finish (see services/sections.py) while
    # the answer is saved; one that already finished is left alone.
    running = await session.scalar(
        update(RoundSession)
        .where(RoundSession.id == answer.session_id, RoundSession.status == RoundStatus.IN_PROGRESS)
        .values(question_shown_at=None)
        .returning(RoundSession.id)
    )

    if running is None:
        return False

    session.add(answer)

    if event:
        outbox.add(session, OutboxEvent, *event)

    await session.flush()

    return True


async def lock_invite_sections(session: AsyncSession, session_id: uuid.UUID) -> list[RoundSession]:
    """Every section of the interview `session_id` belongs to, with its answers, locked
    together and read afresh, so two finishing at once still announce the interview exactly
    once."""
    invite_id = await session.scalar(
        select(RoundSession.candidate_invite_id).where(RoundSession.id == session_id)
    )

    return list(
        await session.scalars(
            select(RoundSession)
            .where(RoundSession.candidate_invite_id == invite_id)
            .options(selectinload(RoundSession.answers))
            .order_by(RoundSession.id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
    )


async def mark_finished(
    session: AsyncSession, row: RoundSession, final_score: int, finished_at: datetime
) -> None:
    """Finishes a locked section with its score."""
    row.status = RoundStatus.FINISHED
    row.final_score = final_score
    row.finished_at = finished_at
    await session.flush()


async def add_event(session: AsyncSession, event_type: str, data: dict) -> None:
    """Keeps the event with the transaction's change, until it's published."""
    outbox.add(session, OutboxEvent, event_type, data)


async def remove_for_invites(session: AsyncSession, candidate_invite_ids: list[uuid.UUID]) -> None:
    """Deletes the candidates' sessions; answers and signals cascade."""
    await session.execute(
        delete(RoundSession).where(RoundSession.candidate_invite_id.in_(candidate_invite_ids))
    )


async def remove_for_interview(sessions, interview_set_id: uuid.UUID) -> None:
    """Deletes every candidate's sessions on the interview, SESSION_DELETE_BATCH at a time, each
    batch in its own transaction (from `sessions`); answers and signals cascade. A run cut off
    keeps what it deleted, and running it again goes on."""
    await delete_in_batches(
        sessions,
        RoundSession,
        RoundSession.interview_set_id == interview_set_id,
        batch=SESSION_DELETE_BATCH,
    )
