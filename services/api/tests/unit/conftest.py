import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from prepza_common.auth.auth import current_user
from prepza_common.auth.user import User
from prepza_common.limits import limits
from prepza_common.redis import memory_cache

from api.config import settings
from api.integrations import companies
from api.main import app
from api.repositories import keys, webhooks
from api.services import key_checks
from tests.unit.ids import CANDIDATE, COMPANY, INTERVIEW, KEY

# The web hook fakes, a fixture of their own module.
from tests.unit.webhook_fakes import endpoints  # noqa: F401


def interview(**changes) -> dict:
    """An interview as companies' internal API returns it."""
    return {
        "id": str(INTERVIEW),
        "title": "Backend",
        "status": "in_process",
        "set_id": str(uuid.uuid4()),
        "pass_mark": 70,
        "candidate_count": 1,
        "created_at": "2026-10-01T09:00:00Z",
        **changes,
    }


def candidate(**changes) -> dict:
    return {
        "id": str(CANDIDATE),
        "email": "anna@example.com",
        "name": "Anna Nowak",
        "status": "finished",
        "progress": 100,
        "grade": 86,
        "passed": True,
        "tab_leaves": 0,
        "copies": 1,
        "fast_answers": 0,
        "created_at": "2026-10-02T10:30:00Z",
        **changes,
    }


@pytest.fixture(autouse=True)
def configured(monkeypatch):
    """Web hooks set up, nothing remembered from another test, and no signed-in user unless a
    test signs one in."""
    monkeypatch.setattr(settings, "api_encryption_key", KEY)
    monkeypatch.setattr(memory_cache, "_entries", {})
    yield
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def limit_hits(monkeypatch):
    """The limit hits recorded (the data of each limit.hit event), never published."""
    hits = []

    async def publish(event_type, data, attempts, timeout):
        hits.append(data)

    monkeypatch.setattr(limits, "publish_retried", publish)

    return hits


def sign_in(uid="u1"):
    app.dependency_overrides[current_user] = lambda: User(
        uid=uid, email=f"{uid}@example.com", email_verified=True, name="Ann"
    )


@pytest.fixture
def companies_api(monkeypatch):
    """The companies service, faked: roles by user in COMPANY, its one interview and candidate,
    the invites it sent, or the status it refuses them with."""
    state = {"roles": {"u1": "owner"}, "sent": [], "refuse": None, "missing": False}

    async def access(company_id, user_id):
        role = state["roles"].get(user_id) if company_id == COMPANY else None

        return {"member": role is not None, "editor": role in ("owner", "admin")}

    def ours(company_id, interview_id):
        if company_id != COMPANY or interview_id != INTERVIEW or state["missing"]:
            raise HTTPException(404, "Interview not found")

    async def interviews(company_id, offset, limit, since=None, after=None):
        return [interview()] if company_id == COMPANY else []

    async def get_interview(company_id, interview_id):
        ours(company_id, interview_id)

        return interview()

    async def candidates(company_id, interview_id, offset, limit, since=None, after=None):
        ours(company_id, interview_id)

        return [candidate()]

    async def get_candidate(company_id, interview_id, invite_id):
        ours(company_id, interview_id)

        return candidate(id=str(invite_id))

    async def invite(
        interview_id, email, sender_id, name=None, return_url=None, sign_in=True, theme=None
    ):
        if state["refuse"]:
            raise HTTPException(state["refuse"], "Refused")

        # Companies returns a candidate already invited as they are (resend false).
        if (interview_id, email, sender_id) in state["sent"]:
            return CANDIDATE, False

        state["sent"].append((interview_id, email, sender_id))
        state.setdefault("names", {})[email] = name
        state.setdefault("options", {})[email] = (return_url, sign_in, theme)

        return CANDIDATE, True

    monkeypatch.setattr(companies, "access", access)
    monkeypatch.setattr(companies, "interviews", interviews)
    monkeypatch.setattr(companies, "interview", get_interview)
    monkeypatch.setattr(companies, "candidates", candidates)
    monkeypatch.setattr(companies, "candidate", get_candidate)
    monkeypatch.setattr(companies, "invite", invite)

    return state


@pytest.fixture
def stored(monkeypatch):
    """Keys and web hooks in memory instead of the database, and requests never rate limited
    unless a test says so (the rate counters asked for are in "counted"). A narrowing that takes
    something away is in "narrowed" as (key id, user id, what it took away), as the action log
    gets it."""
    state = {
        "keys": [],
        "webhooks": [],
        "used": [],
        "limited": False,
        "counted": [],
        "narrowed": [],
    }

    async def by_hash(session, hashed):
        return next((key for key in state["keys"] if key.hash == hashed), None)

    async def used(session, key_id):
        state["used"].append(key_id)

    async def add_key(
        session, company_id, name, shown, hashed, user_id, expires_at, permissions, ips, limit
    ):
        if sum(key.company_id == company_id for key in state["keys"]) >= limit:
            return None

        key = SimpleNamespace(
            id=uuid.uuid4(),
            company_id=company_id,
            name=name,
            shown=shown,
            hash=hashed,
            created_by=user_id,
            created_at=datetime.now(UTC),
            expires_at=expires_at,
            last_used_at=None,
            permissions=permissions,
            allowed_ips=ips,
        )
        state["keys"].append(key)

        return key

    async def keys_of(session, company_id):
        return [key for key in state["keys"] if key.company_id == company_id]

    async def get_key(session, company_id, key_id):
        return next((key for key in await keys_of(session, company_id) if key.id == key_id), None)

    async def narrow(session, company_id, key_id, permissions, user_id):
        key = await get_key(session, company_id, key_id)

        if key is None or not set(permissions) <= set(key.permissions):
            return None

        removed = [item for item in key.permissions if item not in permissions]

        if removed:
            state["narrowed"].append((key.id, user_id, removed))

        key.permissions = permissions

        return key

    async def set_allowed_ips(session, company_id, key_id, ips, user_id):
        key = await get_key(session, company_id, key_id)

        if key is not None:
            key.allowed_ips = ips

        return key

    async def add_webhook(session, company_id, url, sealed, user_id, limit):
        if sum(hook.company_id == company_id for hook in state["webhooks"]) >= limit:
            return None

        hook = SimpleNamespace(
            id=uuid.uuid4(),
            company_id=company_id,
            url=url,
            secret=sealed,
            created_by=user_id,
            created_at=datetime.now(UTC),
            failing=False,
            stopped=False,
        )
        state["webhooks"].append(hook)

        return hook

    async def webhooks_of(session, company_id):
        return [hook for hook in state["webhooks"] if hook.company_id == company_id]

    async def hit(redis, key, name, message="Too many requests. Try again later.", **whose):
        state["counted"].append(key)

        if state["limited"]:
            raise HTTPException(429, message)

    monkeypatch.setattr(keys, "by_hash", by_hash)
    monkeypatch.setattr(keys, "used", used)
    monkeypatch.setattr(keys, "add", add_key)
    monkeypatch.setattr(keys, "of_company", keys_of)
    monkeypatch.setattr(keys, "get", get_key)
    monkeypatch.setattr(keys, "narrow", narrow)
    monkeypatch.setattr(keys, "set_allowed_ips", set_allowed_ips)
    monkeypatch.setattr(webhooks, "add", add_webhook)
    monkeypatch.setattr(webhooks, "of_company", webhooks_of)
    monkeypatch.setattr(key_checks, "hit_or_skip", hit)

    return state
