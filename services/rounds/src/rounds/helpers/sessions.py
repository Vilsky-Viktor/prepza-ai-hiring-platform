from datetime import datetime, timedelta

from rounds.helpers.rounds import next_question
from rounds.models.sessions import Session
from rounds.schemas.sessions import SessionOut, SessionTopicOut


def answer_seconds(shown_at: datetime | None, answered_at: datetime) -> int | None:
    """Whole seconds the answer took; None when the question was never marked as shown."""
    if shown_at is None:
        return None

    return max(0, round((answered_at - shown_at).total_seconds()))


def question_deadline(row: Session) -> datetime | None:
    """When the question on screen counts as wrong; None when untimed or nothing is shown."""
    if row.question_seconds is None or row.question_shown_at is None:
        return None

    return row.question_shown_at + timedelta(seconds=row.question_seconds)


def time_is_up(row: Session, now: datetime, grace_seconds: int = 0) -> bool:
    deadline = question_deadline(row)

    return deadline is not None and now > deadline + timedelta(seconds=grace_seconds)


def seconds_left(row: Session, now: datetime) -> float | None:
    deadline = question_deadline(row)

    return None if deadline is None else max(0.0, (deadline - now).total_seconds())


def topic_out(row: Session) -> SessionTopicOut:
    return SessionTopicOut(
        id=row.id,
        topic_title=row.topic_title,
        status=row.status,
        total=len(row.questions),
        answered=len(row.answers),
    )


def session_out(
    row: Session, interview_title: str | None = None, language: str | None = None
) -> SessionOut:
    return SessionOut(
        id=row.id,
        topic_id=row.topic_id,
        candidate_invite_id=row.candidate_invite_id,
        topic_title=row.topic_title,
        interview_title=interview_title,
        language=language,
        practice=bool(row.practice),
        status=row.status,
        total=len(row.questions),
        answered=len(row.answers),
        started_at=row.started_at,
        finished_at=row.finished_at,
        question_seconds=row.question_seconds,
    )


# Sessions use the same next-question shape as rounds.
next_session_question = next_question
