"""A candidate's own interview mode (and extra time, fixed at the same start) against the real
database: set with the invite or on their page, kept only when apart from the interview's,
recorded in the action log, refused in a language voice mode doesn't speak, and fixed once they
start, also when a change races the start that makes their sessions. Each test makes its own
company and deletes it."""

import os
import uuid

import httpx
import pytest
from fastapi import HTTPException
from prepza_common.auth.user import User
from prepza_common.db.lock_waits import hold_first_commit, race
from prepza_common.events.audit_actions import AuditAction
from prepza_common.i18n.i18n import CodedError
from sqlalchemy import select

from companies.core.db import Session
from companies.integrations import library, rounds
from companies.models.audit import AuditEvent
from companies.repositories import interviews, invite_progress, invites
from companies.services import candidate_changes, candidate_start
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


@pytest.fixture
def sessions_made(monkeypatch):
    """Library's questions and rounds' sessions, faked: what rounds was asked to make."""
    made = []

    async def ready(interview):
        interview.set_id = interview.set_id or uuid.uuid4()

        return interview

    async def content(set_id):
        return {"id": str(set_id), "topics": [{"id": "t", "title": "Python", "questions": []}]}

    async def create(payload):
        made.append((payload["question_seconds"], payload["voice"]))

        return []

    monkeypatch.setattr(candidate_start, "attach_set", ready)
    monkeypatch.setattr(library, "get_content", content)
    monkeypatch.setattr(rounds, "create_sessions", create)

    return made


def starting(invite):
    return User(uid=f"uid-{invite.id}", email=invite.email, email_verified=True)


@pytest.mark.parametrize(
    ("change", "stored"),
    [({"voice": True}, ("voice", None)), ({"extra_time": 50}, ("extra_time", 0))],
)
def test_a_change_racing_the_start_that_makes_the_sessions_is_refused(
    run, monkeypatch, sessions_made, change, stored
):
    """The start holds the invite while it marks it as starting; the change waits on it, then
    finds it starting and is refused, so the sessions (click, 60 seconds) and the invite agree."""

    async def scenario():
        company, interview, invite, owner = await a_candidate()
        held = hold_first_commit(monkeypatch, candidate_start)
        _, refused = await race(
            os.environ["DATABASE_URL"],
            held,
            candidate_start.start_sessions(invite, interview, starting(invite)),
            candidate_changes.change(interview, invite, change, owner),
        )
        kept = getattr(await transaction(invites.get, invite.id), stored[0])
        await factories.deleted(company.id)

        return refused, kept

    refused, kept = run(scenario())

    assert (refused.status_code, refused.code) == (409, "candidate_started")
    assert kept == stored[1]
    assert sessions_made == [(60, False)]


@pytest.mark.parametrize("change", [{"voice": True}, {"extra_time": 50}])
def test_a_change_saved_just_before_the_start_is_in_the_sessions(
    run, monkeypatch, sessions_made, change
):
    """The change holds the invite; the start waits on it, then reads the invite as changed."""

    async def scenario():
        company, interview, invite, owner = await a_candidate()
        held = hold_first_commit(monkeypatch, candidate_changes)
        changed, _ = await race(
            os.environ["DATABASE_URL"],
            held,
            candidate_changes.change(interview, invite, change, owner),
            candidate_start.start_sessions(invite, interview, starting(invite)),
        )
        await factories.deleted(company.id)

        return changed

    assert run(scenario()) is None
    assert sessions_made == [(90, False) if "extra_time" in change else (60, True)]


def test_a_start_rounds_refused_leaves_the_mode_free_to_change(run, monkeypatch, sessions_made):
    async def scenario():
        company, interview, invite, owner = await a_candidate()

        async def refused(payload):
            request = httpx.Request("POST", "http://rounds/internal/sessions")

            raise httpx.HTTPStatusError("refused", request=request, response=httpx.Response(500))

        monkeypatch.setattr(rounds, "create_sessions", refused)

        with pytest.raises(httpx.HTTPStatusError):
            await candidate_start.start_sessions(invite, interview, starting(invite))

        await candidate_changes.change(interview, invite, {"voice": True}, owner)
        stored = await transaction(invites.get, invite.id)
        await factories.deleted(company.id)

        return stored.starting_at, stored.voice

    assert run(scenario()) == (None, True)
