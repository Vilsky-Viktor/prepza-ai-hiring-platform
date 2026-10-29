import uuid
from datetime import datetime, timedelta

from rounds.constants.rounds import RoundStatus
from rounds.helpers.question_times import add_times
from rounds.helpers.rounds import next_question, shuffled
from rounds.models.sessions import Session
from rounds.schemas.library import TopicQuestions
from rounds.schemas.sessions import SessionOut, SessionTopicOut


def new_sections(
    user_id: str,
    candidate_invite_id: uuid.UUID,
    topics: list[TopicQuestions],
    question_seconds: int | None,
    now: datetime,
    preview: bool = False,
    practice: bool = False,
    company_id: uuid.UUID | None = None,
) -> list[Session]:
    """One running section a topic, with its questions in the candidate's own order, each with its
    own time fitted to `question_seconds`, the average (helpers/question_times.py). Each starts
    a microsecond after the one before, so the sections keep the topics' order wherever they're
    listed (repositories/sessions.py list_for_invite)."""
    drawn = [
        shuffled([question.model_dump(mode="json") for question in topic.questions])
        for topic in topics
    ]
    add_times([question for questions in drawn for question in questions], question_seconds)

    return [
        Session(
            user_id=user_id,
            topic_id=topic.id,
            interview_set_id=topic.preparation_id,
            candidate_invite_id=candidate_invite_id,
            company_id=company_id,
            topic_title=topic.title,
            status=RoundStatus.IN_PROGRESS,
            questions=questions,
            final_score=None,
            finished_at=None,
            question_seconds=question_seconds,
            preview=preview,
            practice=practice,
            started_at=now + timedelta(microseconds=position),
            answers=[],
        )
        for position, (topic, questions) in enumerate(zip(topics, drawn, strict=True))
    ]


def answer_seconds(shown_at: datetime | None, answered_at: datetime) -> int | None:
    """Whole seconds the answer took; None when the question was never marked as shown."""
    if shown_at is None:
        return None

    return max(0, round((answered_at - shown_at).total_seconds()))


def question_deadline(row: Session) -> datetime | None:
    """When the question on screen counts as wrong, from its own time; None when untimed or
    nothing is shown."""
    question = next_question(row) if row.question_shown_at else None

    if question is None or question.seconds is None:
        return None

    return row.question_shown_at + timedelta(seconds=question.seconds)


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
