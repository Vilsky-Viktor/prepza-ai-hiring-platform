"""An owner or admin's changes to an interview: its settings, title, topics' number of
questions and shareable link. Each is saved with its line in the action log."""

import secrets
from uuid import UUID

from fastapi import HTTPException, status
from prepza_common.events.audit_actions import AuditAction

from companies.constants.interviews import NO_QUESTIONS_LEFT, SETTINGS_LOGGED
from companies.constants.invites import INTERVIEW_NOT_READY, LINK_TOKEN_BYTES
from companies.core.db import Session
from companies.helpers.interviews import interview_questions
from companies.integrations import library
from companies.models.interviews import Interview
from companies.repositories import audit, interviews
from companies.schemas.interviews import InterviewSettings
from companies.services.interview_access import ready_for_invites


async def update_settings(
    interview: Interview, settings: InterviewSettings, user_id: str, via: str | None
) -> None:
    """Saves the settings that were sent, with a line in the log for a changed setting and one
    for a changed pass mark."""
    sent = settings.model_dump(include=SETTINGS_LOGGED, exclude_none=True)

    async with Session.begin() as session:
        await interviews.update_settings(session, interview.id, settings)

        if any(value != getattr(interview, key) for key, value in sent.items()):
            await audit.record_interview(
                session, interview, user_id, AuditAction.INTERVIEW_SETTINGS_CHANGED
            )

        if settings.pass_mark is not None and settings.pass_mark != interview.pass_mark:
            await audit.record_interview(
                session, interview, user_id, AuditAction.PASS_MARK_CHANGED, via
            )


async def rename(interview: Interview, title: str, user_id: str) -> None:
    """Once it has been generated (409 before): its questions' set is renamed in library first."""
    if interview.set_id is None:
        raise HTTPException(status.HTTP_409_CONFLICT, INTERVIEW_NOT_READY)

    await library.rename_set(interview.set_id, title)

    async with Session.begin() as session:
        await interviews.set_title(session, interview.id, title)
        await audit.record_interview(session, interview, user_id, AuditAction.INTERVIEW_RENAMED)


async def set_topic_limit(interview: Interview, topic_id: UUID, limit: int, user_id: str) -> None:
    """How many of the topic's questions each candidate gets: at most the topic has (422), and
    every candidate gets at least one question (422)."""
    found = await library.get_set(interview.set_id) or {}
    topic = next(
        (item for item in found.get("topics", []) if str(item["id"]) == str(topic_id)), None
    )

    if topic is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Topic not found")

    if limit > topic["question_count"]:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            f"The topic has only {topic['question_count']} questions",
        )

    # Every candidate gets at least one question.
    def keeps_questions(limits: dict[str, int]) -> bool:
        return bool(interview_questions(found, limits))

    async with Session.begin() as session:
        saved = await interviews.set_topic_limit(
            session, interview.id, topic_id, limit, keeps_questions
        )

        if saved:
            await audit.record_interview(
                session, interview, user_id, AuditAction.INTERVIEW_SETTINGS_CHANGED
            )

    if not saved:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, NO_QUESTIONS_LEFT)


async def set_link(interview: Interview, on: bool, user_id: str) -> str | None:
    """Turns the link on (a new code, kept while it stays on) or off (it stops working at once).
    On only once it has its questions, as for an invite: visitors could otherwise hold credits
    for an interview they can't start. Returns its code."""
    if on:
        await ready_for_invites(interview, user_id)

    token = (interview.link_token or secrets.token_urlsafe(LINK_TOKEN_BYTES)) if on else None
    action = AuditAction.LINK_TURNED_ON if on else AuditAction.LINK_TURNED_OFF

    async with Session.begin() as session:
        await interviews.set_link(session, interview.id, token)
        await audit.record_interview(session, interview, user_id, action)

    return token
