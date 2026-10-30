from datetime import UTC, datetime

from prepza_common.auth.user import User

from rounds.constants.rounds import RoundStatus
from rounds.core.db import Session as Db
from rounds.helpers.sessions import (
    following_question,
    next_session_question,
    seconds_left,
    time_is_up,
    topic_out,
)
from rounds.models.sessions import Session
from rounds.repositories import sessions
from rounds.schemas.interview_flow import InterviewStep
from rounds.schemas.rounds import NextQuestion
from rounds.services import outbox as outbox_service
from rounds.services import sections, voice_session
from rounds.services.session_access import get_owned_session, own_sections, read
from rounds.services.session_expiry import finish_if_expired
from rounds.services.session_titles import session_out_titled


async def move_on(done: list[Session], shown: Session | None) -> None:
    """One save for a step: the sections left with no question finish, and the next one's
    waiting question starts its clock (kept on the section), in voice mode too, as it starts
    being read aloud. The finished sections' events are published after it."""
    async with Db.begin() as session:
        await sections.finish_open(session, done)

        if shown is not None and shown.question_shown_at is None:
            shown.question_shown_at = await sessions.mark_shown(session, shown.id)

    if done:
        await outbox_service.flush_quietly()


async def interview_step(row: Session, user: User) -> InterviewStep:
    """The step after the last one: the first open section's waiting question, starting its
    clock. A section with no question left is finished on the way, with the next question's
    clock; with none open, the interview is done. The sections are loaded once; only after a
    change (a time-out, a finish) are they read again."""
    sections_now = await own_sections(row)
    running = [section for section in sections_now if section.status == RoundStatus.IN_PROGRESS]
    # get_owned_session checked the interview's time only if this section was running.
    changed = bool(
        running
        and row.status != RoundStatus.IN_PROGRESS
        and await finish_if_expired(row.candidate_invite_id)
    )
    done = []

    for section in running:
        # Reloaded: a question whose time ran out counts as wrong, an expired interview ends.
        if changed or time_is_up(section, datetime.now(UTC)):
            section = await get_owned_session(section.id, user)
            changed = True

            if section.status != RoundStatus.IN_PROGRESS:
                continue

        question = next_session_question(section)

        if question is None:
            done.append(section)
            changed = True

            continue

        # Voice mode: the clock starts once the question's reading is ready to play.
        await voice_session.clip_ready(section, question)
        await move_on(done, section)
        question.seconds_left = seconds_left(section, datetime.now(UTC))
        question.last = following_question(section, sections_now) is None

        return await step_out(section, user, question, None if changed else sections_now)

    await move_on(done, None)

    if not changed:
        return await step_out(row, user, None, sections_now)

    return await step_out(await read(row.id), user, None)


async def finish_interview(row: Session, user: User) -> InterviewStep:
    """The candidate ends the interview: every open section finishes, in one save; unanswered
    questions count as wrong."""
    open_sections = await own_sections(row)

    async with Db.begin() as session:
        await sections.finish_open(session, open_sections)

    await outbox_service.flush_quietly()

    return await step_out(await read(row.id), user, None)


async def step_out(
    section: Session,
    user: User,
    question: NextQuestion | None,
    sections_now: list[Session] | None = None,
) -> InterviewStep:
    """`sections_now`: the interview's, when they're current; read again without them."""
    topics = [topic_out(item) for item in sections_now or await own_sections(section)]

    return InterviewStep(
        session=await session_out_titled(section),
        question=question,
        topics=topics,
        done=question is None and all(t.status == RoundStatus.FINISHED for t in topics),
    )
