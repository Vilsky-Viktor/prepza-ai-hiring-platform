"""A candidate's own interview mode against the real database: set with the invite or on their
page, kept only when apart from the interview's, recorded in the action log, refused in a
language voice mode doesn't speak, and fixed once they start, also when they start between the
page's read and the change. Each test makes its own company and deletes it."""

import uuid

import pytest
from fastapi import HTTPException
from prepza_common.events.audit_actions import AuditAction
from prepza_common.i18n.i18n import CodedError
from sqlalchemy import select

from companies.core.db import Session
from companies.models.audit import AuditEvent
from companies.repositories import interviews, invite_progress, invites
from companies.services import candidate_changes
from tests.integration import factories
from tests.integration.transactions import transaction


async def a_candidate(language: str = "en") -> tuple:
    """A company's click-mode interview in `language`, and one candidate invited to it."""
    tag = uuid.uuid4()
    company = await factories.company(f"Modes {tag}", f"ann-{tag}", f"ann-{tag}@example.com")
    interview = await transaction(interviews.create, company.id, uuid.uuid4(), language, 60)
    invite, _ = await transaction(
        invites.upsert, interview.id, f"cara-{tag}@example.com", "Backend", "Acme", language
    )

    return company, interview, invite, f"ann-{tag}"


async def actions(company_id) -> list[str]:
    async with Session() as session:
        query = select(AuditEvent.action).where(AuditEvent.company_id == company_id)

        return list(await session.scalars(query))


def test_a_candidates_mode_is_set_kept_apart_and_logged(run):
    async def scenario():
        company, interview, invite, owner = await a_candidate()
        await candidate_changes.change(interview, invite, {"voice": True}, owner)
        by_voice = (await transaction(invites.get, invite.id)).voice
        # The interview's own mode: they follow the interview's again.
        await candidate_changes.change(interview, invite, {"voice": False}, owner)
        following = (await transaction(invites.get, invite.id)).voice
        logged = await actions(company.id)
        await factories.deleted(company.id)

        return by_voice, following, logged

    by_voice, following, logged = run(scenario())

    assert (by_voice, following) == (True, None)
    assert logged.count(AuditAction.CANDIDATE_MODE_SET) == 2


def test_a_candidate_who_started_since_the_page_was_read_keeps_their_mode(run):
    async def scenario():
        company, interview, invite, owner = await a_candidate()
        # The page read Ann as invited; she starts before the change arrives.
        await transaction(invite_progress.start, invite.id, "cara-uid")

        with pytest.raises(HTTPException) as refused:
            await candidate_changes.change(interview, invite, {"voice": True}, owner)

        stored = (await transaction(invites.get, invite.id)).voice
        logged = await actions(company.id)
        await factories.deleted(company.id)

        return refused.value, stored, logged

    refused, stored, logged = run(scenario())

    assert (refused.status_code, refused.code) == (409, "candidate_started")
    assert stored is None
    assert AuditAction.CANDIDATE_MODE_SET not in logged


def test_voice_is_refused_in_a_language_voice_mode_doesnt_speak(run):
    async def scenario():
        company, interview, invite, owner = await a_candidate("ja")

        with pytest.raises(CodedError) as refused:
            await candidate_changes.change(interview, invite, {"voice": True}, owner)

        stored = (await transaction(invites.get, invite.id)).voice
        await factories.deleted(company.id)

        return refused.value, stored

    refused, stored = run(scenario())

    assert (refused.status_code, refused.code) == (422, "voice_unavailable")
    assert stored is None


def test_an_invite_sets_the_mode_until_the_candidate_starts(run):
    async def scenario():
        company, interview, invite, _ = await a_candidate()
        email = invite.email
        sent = (interview.id, email, "Backend", "Acme", "en")
        await transaction(invites.upsert, *sent, mode_chosen=True, voice=True)
        chosen = (await transaction(invites.get, invite.id)).voice
        # Sent again without a mode: theirs stays.
        await transaction(invites.upsert, *sent)
        kept = (await transaction(invites.get, invite.id)).voice
        # Started: sending again never changes how they take it.
        await transaction(invite_progress.start, invite.id, "cara-uid")
        await transaction(invites.upsert, *sent, mode_chosen=True, voice=False)
        started = (await transaction(invites.get, invite.id)).voice
        await factories.deleted(company.id)

        return chosen, kept, started

    assert run(scenario()) == (True, True, True)
