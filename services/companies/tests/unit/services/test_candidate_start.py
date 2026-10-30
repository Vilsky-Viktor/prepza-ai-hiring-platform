import asyncio
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

import httpx
import pytest
from fastapi import HTTPException
from prepza_common.auth.user import User

from companies.integrations import library, rounds
from companies.repositories import invite_progress
from companies.services import candidate_start

USER = User(uid="cand", email="cand@example.com", email_verified=True)

INVITE = SimpleNamespace(
    id=uuid.uuid4(),
    extra_time=0,
    interview_id=uuid.uuid4(),
    email="cand@example.com",
    hold_key="k",
    voice=None,
    status="invited",
    starting_at=None,
)
MARKED_AT = datetime(2026, 10, 30, 9, tzinfo=UTC)
INTERVIEW = SimpleNamespace(
    set_id=uuid.uuid4(), company_id=uuid.uuid4(), question_seconds=60, topic_limits={}, voice=False
)


@pytest.fixture
def steps(monkeypatch):
    """What happened, in order, as a candidate starts."""
    done = []

    async def same(interview):
        return interview

    async def content(set_id):
        return {"id": str(set_id), "topics": [{"id": "t", "title": "Python", "questions": []}]}

    async def create(payload):
        done.append(("sessions", payload["question_seconds"], payload["voice"]))

        return [{"id": str(uuid.uuid4()), "topic_title": "Python", "status": "in_progress"}]

    async def mark(session, invite_id):
        done.append("marked")

        # As stored now: the company gave extra time and voice before the start marked it.
        return SimpleNamespace(
            **{**vars(INVITE), "extra_time": 50, "voice": True, "starting_at": MARKED_AT}
        )

    async def clear(session, invite_id, starting_at):
        done.append(("cleared", starting_at))

    async def start(session, invite_id, user_id, name=None):
        done.append("started")

        return "invited"

    async def erase(invite_ids):
        done.append("erased")

    monkeypatch.setattr(candidate_start, "attach_set", same)
    monkeypatch.setattr(library, "get_content", content)
    monkeypatch.setattr(rounds, "create_sessions", create)
    monkeypatch.setattr(rounds, "delete_invite_sessions", erase)
    monkeypatch.setattr(invite_progress, "mark_starting", mark)
    monkeypatch.setattr(invite_progress, "clear_starting", clear)
    monkeypatch.setattr(invite_progress, "start", start)

    return done


def test_the_invite_is_marked_started_once_its_sessions_exist(steps):
    out = asyncio.run(candidate_start.start_sessions(INVITE, INTERVIEW, USER))

    assert [row.topic_title for row in out.sessions] == ["Python"]
    # Made with the values stored when the start marked the invite, not those read before.
    assert steps == ["marked", ("sessions", 90, True), "started"]


def test_rounds_failing_leaves_the_invite_unstarted_so_expiry_frees_its_credits(steps, monkeypatch):
    async def down(payload):
        raise httpx.ConnectError("rounds is down")

    monkeypatch.setattr(rounds, "create_sessions", down)

    with pytest.raises(httpx.ConnectError):
        asyncio.run(candidate_start.start_sessions(INVITE, INTERVIEW, USER))

    # Unreachable, rounds may have made them: the mark stays, and starting again finishes it.
    assert steps == ["marked"]


def test_rounds_refusing_lifts_the_starting_mark(steps, monkeypatch):
    """Rounds answered and made nothing: the company may change extra time or the mode again."""

    async def refused(payload):
        request = httpx.Request("POST", "http://rounds/internal/sessions")

        raise httpx.HTTPStatusError("refused", request=request, response=httpx.Response(500))

    monkeypatch.setattr(rounds, "create_sessions", refused)

    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(candidate_start.start_sessions(INVITE, INTERVIEW, USER))

    assert steps == ["marked", ("cleared", MARKED_AT)]


def test_an_invite_revoked_before_its_start_makes_no_sessions(steps, monkeypatch):
    async def gone(session, invite_id):
        return None

    monkeypatch.setattr(invite_progress, "mark_starting", gone)

    with pytest.raises(HTTPException) as refused:
        asyncio.run(candidate_start.start_sessions(INVITE, INTERVIEW, USER))

    assert refused.value.status_code == 404
    assert steps == []


def test_an_invite_revoked_while_starting_loses_its_sessions(steps, monkeypatch):
    async def gone(session, invite_id, user_id, name=None):
        return None

    monkeypatch.setattr(invite_progress, "start", gone)

    with pytest.raises(HTTPException) as refused:
        asyncio.run(candidate_start.start_sessions(INVITE, INTERVIEW, USER))

    assert refused.value.status_code == 404
    assert steps == ["marked", ("sessions", 90, True), "erased"]


def test_an_invite_that_expired_while_starting_has_its_credits_set_aside_again(steps, monkeypatch):
    """Expiry gave them back after the invite was read; otherwise it finishes uncharged."""
    held = []

    async def expired(session, invite_id, user_id, name=None):
        steps.append("started")

        return "expired"

    async def hold_again(invite, key):
        held.append(key)

    monkeypatch.setattr(invite_progress, "start", expired)
    monkeypatch.setattr(candidate_start, "hold_again", hold_again)
    asyncio.run(candidate_start.start_sessions(INVITE, INTERVIEW, USER))

    assert held == ["k"]


def test_an_invite_started_as_read_isnt_held_again(steps, monkeypatch):
    held = []

    async def hold_again(invite, key):
        held.append(key)

    monkeypatch.setattr(candidate_start, "hold_again", hold_again)
    asyncio.run(candidate_start.start_sessions(INVITE, INTERVIEW, USER))

    assert held == []
