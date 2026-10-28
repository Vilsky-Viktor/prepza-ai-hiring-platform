import uuid
from datetime import UTC, datetime

import pytest
from cryptography.fernet import Fernet
from fastapi import HTTPException

from ats.config import settings
from ats.integrations import companies, workable
from ats.integrations.errors import KeyRejected
from ats.main import app
from ats.models.ats import AtsConnection
from ats.repositories import ats, ats_candidates, ats_links
from ats.services import ats as ats_service
from tests.unit.workable_setup import (
    COMPANY_ID,
    INTERVIEW_ID,
    JOBS,
    OTHER_COMPANY,
    STAGES,
    THEIR_INTERVIEW,
)

EDITORS = ("owner", "admin")


def interview(company_id, title="Accountant", ready=True, interview_id=None) -> dict:
    """An interview as companies' GET /internal/interviews returns it."""
    return {
        "id": str(interview_id or uuid.uuid4()),
        "company_id": str(company_id),
        "title": title,
        "ready": ready,
    }


@pytest.fixture
def companies_api(monkeypatch):
    """The companies service, faked: members' roles by (company, user), interviews by id, and
    the invites it sent (or the status it refuses them with)."""
    state = {"roles": {}, "interviews": {}, "sent": [], "refuse": None}

    async def access(company_id, user_id):
        role = state["roles"].get((company_id, user_id))

        return {"member": role is not None, "editor": role in EDITORS}

    async def interviews(ids):
        return {item: state["interviews"][item] for item in ids if item in state["interviews"]}

    async def invite(interview_id, email, sender_id, name=None):
        if state["refuse"]:
            raise HTTPException(state["refuse"])

        state["sent"].append((email, sender_id))
        state.setdefault("names", {})[email] = name

        return uuid.uuid4()

    monkeypatch.setattr(companies, "access", access)
    monkeypatch.setattr(companies, "interviews", interviews)
    monkeypatch.setattr(companies, "invite", invite)

    return state


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def key(monkeypatch):
    """Integrations set up: an encryption key."""
    value = Fernet.generate_key().decode()
    monkeypatch.setattr(settings, "ats_encryption_key", value)

    return value


@pytest.fixture
def stored(monkeypatch, companies_api):
    """A company with an admin and a viewer, an interview of its own and one of another
    company's, its ATS rows kept in memory, and Workable answering with one job and one stage
    for the token "good"."""
    companies_api["roles"] = {(COMPANY_ID, "ann"): "admin", (COMPANY_ID, "vic"): "viewer"}
    companies_api["interviews"] = {
        INTERVIEW_ID: interview(COMPANY_ID, interview_id=INTERVIEW_ID),
        THEIR_INTERVIEW: interview(OTHER_COMPANY, "Theirs", interview_id=THEIR_INTERVIEW),
    }
    rows = {"connection": None, "links": [], "subscriptions": [], "targets": [], "read": []}
    # Connections made, as the ATS_CONNECTS_PER_HOUR limit counts them (no Redis in unit tests).
    rows["connects"] = []

    async def count(redis, key, name, message=None, **who):
        rows["connects"].append((key, name, who["user_id"]))

    monkeypatch.setattr(ats_service, "hit_or_skip", count)

    async def connect(
        session, company_id, provider, account, credentials, user_id, member_id=None, language=None
    ):
        rows["connection"] = AtsConnection(
            member_id=member_id,
            language=language,
            id=uuid.uuid4(),
            company_id=company_id,
            provider=provider,
            account=account,
            credentials=credentials,
            status="connected",
            created_by=user_id,
            created_at=datetime.now(UTC),
        )

    async def connection(session, company_id, provider):
        return rows["connection"]

    async def connections(session, company_id):
        return [rows["connection"]] if rows["connection"] else []

    async def disconnect(session, company_id, provider, user_id=None):
        rows["connection"] = None
        # Who disconnected it, for the action log (None when prepza undid its own connect).
        rows.setdefault("disconnected_by", []).append(user_id)

    async def add_link(session, company_id, connection_id, interview_id, job, stage, user_id):
        rows["links"].append((interview_id, job["id"], stage["id"], user_id))

        return uuid.uuid4()

    async def set_subscription(session, link_id, subscription_id):
        rows["subscriptions"].append(subscription_id)

    async def subscriptions(session, company_id, link_id=None):
        return list(rows["subscriptions"])

    async def no_counts(session, company_id):
        return {}

    async def member_id(subdomain, token, email):
        return "member-1"

    async def subscribe(subdomain, token, target, job_id, stage_id):
        rows["targets"].append(target)

        return "sub-1"

    async def check(subdomain, token):
        if token != "good":
            raise KeyRejected

    async def jobs(subdomain, token):
        rows["read"].append("every job")

        return JOBS

    async def job(subdomain, token, job_id):
        rows["read"].append(job_id)

        return {"name": "Accountant", "sections": []}

    async def stages(subdomain, token, job_id):
        return STAGES

    for name, fake in {
        "connect": connect,
        "connection": connection,
        "connections": connections,
        "disconnect": disconnect,
    }.items():
        monkeypatch.setattr(ats, name, fake)
    monkeypatch.setattr(ats_links, "add_link", add_link)
    monkeypatch.setattr(ats_links, "set_subscription", set_subscription)
    monkeypatch.setattr(ats_links, "subscriptions", subscriptions)
    monkeypatch.setattr(workable, "check", check)
    monkeypatch.setattr(workable, "jobs", jobs)
    monkeypatch.setattr(workable, "job", job)
    monkeypatch.setattr(workable, "stages", stages)
    monkeypatch.setattr(workable, "member_id", member_id)
    monkeypatch.setattr(workable, "subscribe", subscribe)
    monkeypatch.setattr(ats_candidates, "counts", no_counts)

    return rows
