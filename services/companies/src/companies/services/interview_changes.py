"""An owner or admin's changes to an interview: its settings, title, topics' number of
questions and shareable link. Each is saved with its line in the action log."""

import secrets
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from prepza_common.events.audit_actions import AuditAction
from prepza_common.events.interviews import INTERVIEW_PRIVACY_CHANGED, InterviewPrivacyChanged

from companies.constants.interviews import NO_QUESTIONS_LEFT, SETTINGS_LOGGED
from companies.constants.invites import INTERVIEW_NOT_READY, LINK_TOKEN_BYTES
from companies.core.db import Session
from companies.helpers.interviews import interview_questions
from companies.integrations import library
from companies.models.interviews import Interview
from companies.repositories import audit, interviews, outbox
from companies.schemas.interviews import InterviewSettings
from companies.services import outbox as outbox_service
from companies.services.interview_access import ready_for_invites
from companies.services.voice_modes import refuse_unspoken


async def update_settings(
    interview: Interview, settings: InterviewSettings, user_id: str, via: str | None
) -> None:
    """Saves the settings that were sent, with a line in the log for a changed setting and one
    for a changed pass mark, and library told of the bank opt-out when it's sent. Voice mode
    only in VOICE_LANGUAGES (422, voice_unavailable)."""
    refuse_unspoken(interview, settings.voice)
    sent = settings.model_dump(include=SETTINGS_LOGGED, exclude_none=True)

    async with Session.begin() as session:
        await interviews.update_settings(session, interview.id, settings)

        if settings.keep_private is not None:
            add_privacy_changed(session, interview, settings.keep_private)

        if any(value != getattr(interview, key) for key, value in sent.items()):
            await audit.record_interview(
                session, interview, user_id, AuditAction.INTERVIEW_SETTINGS_CHANGED
            )

        if settings.pass_mark is not None and settings.pass_mark != interview.pass_mark:
            await audit.record_interview(
                session, interview, user_id, AuditAction.PASS_MARK_CHANGED, via
            )

    if settings.keep_private is not None:
        await outbox_service.flush_quietly()


def add_privacy_changed(session, interview: Interview, keep_private: bool) -> None:
    """interview.privacy_changed, sent whenever the opt-out is (repeating the state is harmless):
    library takes the interview's questions out of the shared bank or lets them back in. Timed
    after the update took the interview's row lock, so of two changes at once the one saved last
    is the newer for library too."""
    data = InterviewPrivacyChanged(
        interview_id=interview.id,
        company_id=interview.company_id,
        set_id=interview.set_id,
        generation_id=interview.generation_id,
        keep_private=keep_private,
        changed_at=datetime.now(UTC),
    )
    outbox.add(session, INTERVIEW_PRIVACY_CHANGED, data.model_dump(mode="json"))


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
