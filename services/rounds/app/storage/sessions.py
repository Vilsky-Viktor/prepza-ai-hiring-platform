import uuid
from datetime import UTC, datetime, timedelta

from prepza_common import outbox
from prepza_common.db import delete_in_batches
from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.constants.events import INTERVIEW_FINISHED, SESSION_SCORED
from app.constants.integrity import (
    FAST_ANSWER_SECONDS,
    MIN_TAB_LEAVE_SECONDS,
    IntegritySignal,
)
from app.constants.rounds import SESSION_DELETE_BATCH, RoundStatus
from app.helpers.rounds import shuffled
from app.helpers.scores import final_score, invite_grade, scored
from app.models.answers import Answer
from app.models.outbox import OutboxEvent
from app.models.sessions import Session
from app.models.signals import Signal
from app.schemas.library import TopicQuestions
from app.storage.db import Session as Db

# Signals are read only for a scorecard (list_for_invite's `signals`).
LOAD_SESSION = [selectinload(Session.answers)]


async def create_many(
    user_id: str,
    candidate_invite_id: uuid.UUID,
    topics: list[TopicQuestions],
    question_seconds: int | None,
    preview: bool = False,
    practice: bool = False,
    company_id: uuid.UUID | None = None,
) -> list[Session]:
    # Each section starts a microsecond after the one before, so the sections keep the topics'
    # order wherever they're listed (see list_for_invite).
    now = datetime.now(UTC)
    rows = [
        Session(
            user_id=user_id,
            topic_id=topic.id,
            interview_set_id=topic.preparation_id,
            candidate_invite_id=candidate_invite_id,
            company_id=company_id,
            topic_title=topic.title,
            status=RoundStatus.IN_PROGRESS,
            questions=shuffled([question.model_dump(mode="json") for question in topic.questions]),
            final_score=None,
            finished_at=None,
            question_seconds=question_seconds,
            preview=preview,
            practice=practice,
            started_at=now + timedelta(microseconds=position),
            answers=[],
        )
        for position, topic in enumerate(topics)
    ]

    async with Db() as session:
        session.add_all(rows)
        await session.commit()

    return rows


async def get(session_id: uuid.UUID) -> Session | None:
    async with Db() as session:
        return await session.get(Session, session_id, options=LOAD_SESSION)


async def list_for_invite(candidate_invite_id: uuid.UUID, signals: bool = False) -> list[Session]:
    query = (
        select(Session)
        .where(Session.candidate_invite_id == candidate_invite_id)
        .options(*LOAD_SESSION, *([selectinload(Session.signals)] if signals else []))
        .order_by(Session.started_at, Session.id)
    )

    async with Db() as session:
        return list(await session.scalars(query))


async def scores_for_invites(invite_ids: list[uuid.UUID]) -> dict[uuid.UUID, dict]:
    """Each candidate's progress, grade, whether they finished, how many answers they picked (not
    timed out: what decides a charge, as in finish()), and their integrity signals, counted in
    the database rather than from every session's questions and answers."""
    if not invite_ids:
        return {}

    invite = Session.candidate_invite_id
    chosen = invite.in_(invite_ids)
    sections_query = (
        select(
            invite,
            func.sum(func.jsonb_array_length(Session.questions)),
            func.bool_and(Session.status == RoundStatus.FINISHED),
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
        .join(Answer, Answer.session_id == Session.id)
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
        .join(Signal, Signal.session_id == Session.id)
        .where(chosen)
        .group_by(invite)
    )

    async with Db() as session:
        sections = (await session.execute(sections_query)).all()
        answers = {row[0]: row[1:] for row in await session.execute(answers_query)}
        signals = {row[0]: row[1:] for row in await session.execute(signals_query)}

    result = {}

    for invite_id, total, finished in sections:
        answered, score_sum, fast_answers, picked = answers.get(invite_id, (0, 0, 0, 0))
        tab_leaves, copies = signals.get(invite_id, (0, 0))
        result[invite_id] = {
            **invite_grade(answered, score_sum or 0, total, finished),
            "tab_leaves": tab_leaves,
            "copies": copies,
            "fast_answers": fast_answers,
            "picked": picked,
        }

    return result


async def mark_shown(session_id: uuid.UUID) -> datetime:
    """Starts the clock on the waiting question and returns when it started; reloading the
    page, or a second tab asking at the same moment, gets the same time."""
    async with Db() as session:
        shown_at = await session.scalar(
            update(Session)
            .where(Session.id == session_id)
            .values(question_shown_at=func.coalesce(Session.question_shown_at, datetime.now(UTC)))
            .returning(Session.question_shown_at)
        )
        await session.commit()

    return shown_at


async def add_answer(answer: Answer, event: tuple[str, dict] | None = None) -> bool:
    """Saves the answer (and its event, when it has one) and stops the clock, so the next
    question starts its own. A question that timed out has no event: nothing was picked.

    False when the section is no longer running, or the question already has an answer, e.g.
    two requests timing out the same question at once.
    """
    async with Db() as session:
        # Stopping the clock locks the section, so it can't finish (see finish) while the answer
        # is saved; one that already finished is left alone.
        running = await session.scalar(
            update(Session)
            .where(Session.id == answer.session_id, Session.status == RoundStatus.IN_PROGRESS)
            .values(question_shown_at=None)
            .returning(Session.id)
        )

        if running is None:
            await session.rollback()

            return False

        session.add(answer)

        if event:
            outbox.add(session, OutboxEvent, *event)

        try:
            await session.commit()
        except IntegrityError:
            return False

    return True


async def finish(session_id: uuid.UUID) -> None:
    """Finishes one section, scored from the answers saved by the time it's locked; unanswered
    questions count as wrong. When it was the interview's last open one, the
    interview.finished event is saved with it, carrying how many answers the candidate
    picked."""
    async with Db() as session:
        invite_id = await session.scalar(
            select(Session.candidate_invite_id).where(Session.id == session_id)
        )
        # The invite's sections are locked together, so two finishing at once still announce
        # the interview exactly once.
        sections = list(
            await session.scalars(
                select(Session)
                .where(Session.candidate_invite_id == invite_id)
                .options(selectinload(Session.answers))
                .order_by(Session.id)
                .with_for_update()
            )
        )
        finishing = next((row for row in sections if row.id == session_id), None)

        if finishing is None or finishing.status != RoundStatus.IN_PROGRESS:
            await session.commit()

            return

        finishing.status = RoundStatus.FINISHED
        finishing.final_score = final_score(
            [answer.score for answer in finishing.answers], len(finishing.questions)
        )
        finishing.finished_at = datetime.now(UTC)

        # A preview says nothing about the questions; nor does a talent's practice round after
        # their first on a template, which is started as one (routers/practice.py).
        if not finishing.preview:
            outbox.add(session, OutboxEvent, SESSION_SCORED, scored(finishing))

        if all(row.status == RoundStatus.FINISHED for row in sections):
            picked = sum(1 for row in sections for answer in row.answers if not answer.timed_out)
            outbox.add(
                session,
                OutboxEvent,
                INTERVIEW_FINISHED,
                {"candidate_invite_id": str(invite_id), "answered": picked},
            )

        await session.commit()


async def remove_for_invites(candidate_invite_ids: list[uuid.UUID]) -> None:
    """Deletes the candidates' sessions; answers and signals cascade."""
    if not candidate_invite_ids:
        return

    async with Db() as session:
        await session.execute(
            delete(Session).where(Session.candidate_invite_id.in_(candidate_invite_ids))
        )
        await session.commit()


async def remove_for_interview(interview_set_id: uuid.UUID) -> None:
    """Deletes every candidate's sessions on the interview, SESSION_DELETE_BATCH at a time, each
    batch in its own transaction; answers and signals cascade. A run cut off keeps what it
    deleted, and running it again goes on."""
    await delete_in_batches(
        Db, Session, Session.interview_set_id == interview_set_id, batch=SESSION_DELETE_BATCH
    )
