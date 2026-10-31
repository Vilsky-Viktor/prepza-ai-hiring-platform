import pytest
from testee_common.auth.auth import current_user
from testee_common.auth.user import User
from testee_common.events.audit_actions import AuditAction, TargetKind
from testee_common.limits import limits
from testee_common.redis import memory_cache

from companies.core.security import REQUEST_VIA
from companies.integrations import billing
from companies.main import app
from companies.repositories import (
    accounts,
    audit,
    batch_deletion,
    candidates,
    companies,
    interview_notes,
    invites,
)
from companies.services import company_deletion, interview_removal
from tests.unit import fake_candidates


@pytest.fixture(autouse=True)
def no_billing_calls(monkeypatch):
    """Billing is another service; tests that care about its calls replace these."""

    async def nothing(*args, **kwargs):
        return None

    async def no_invites(session, user_id, email):
        return []

    for name in ("delete_company", "release_candidate", "charge_candidate", "welcome_company"):
        monkeypatch.setattr(billing, name, nothing)

    async def none_unfinished(session, interview_id, after, size):
        return []

    monkeypatch.setattr(accounts, "unfinished_invites", no_invites)
    monkeypatch.setattr(invites, "unfinished", none_unfinished)


@pytest.fixture(autouse=True)
def nothing_to_delete_in_batches(monkeypatch):
    """Batched deletions (a company's or an interview's invites, interviews and action log) find
    nothing: unit tests have no database; the integration tests delete for real."""

    async def no_invites(session, *conditions):
        return 0, []

    async def no_interviews(session, company_id):
        return 0

    async def no_log(sessions, company_id):
        pass

    monkeypatch.setattr(batch_deletion, "delete_invites_batch", no_invites)
    monkeypatch.setattr(batch_deletion, "delete_interviews_batch", no_interviews)
    monkeypatch.setattr(audit, "delete_company", no_log)

    async def no_notes(sessions, model, *conditions):
        pass

    monkeypatch.setattr(interview_removal, "delete_in_batches", no_notes)
    monkeypatch.setattr(company_deletion, "delete_in_batches", no_notes)


@pytest.fixture(autouse=True)
def no_notes_by_default(monkeypatch):
    """Interviews have no notes unless a test says (unit tests have no database)."""

    async def none(session, interview_ids):
        return {}

    monkeypatch.setattr(interview_notes, "summaries", none)


@pytest.fixture(autouse=True)
def no_company_by_default(monkeypatch):
    """Looking a company up finds none unless a test stores one (unit tests have no database)."""

    async def none(session, company_id):
        return None

    monkeypatch.setattr(companies, "get", none)


@pytest.fixture(autouse=True)
def audited(monkeypatch):
    """The action log, in memory: (company id, user id, action, target id, target kind) as
    recorded, with via after them when it's set (by the caller or the request). An interview's actions (record_interview) and
    results views (record_view) land here too."""
    events = []

    async def record(
        session, company_id, user_id, action, target_id=None, via=None, target_kind=None, **_
    ):
        # As the real one: what the request came through, unless the caller says.
        via = via or REQUEST_VIA.get()
        events.append(
            (company_id, user_id, action, target_id, target_kind, *([via] if via else []))
        )

    async def record_interview(session, interview, user_id, action, via=None):
        await record(
            session, interview.company_id, user_id, action, interview.id, via, TargetKind.INTERVIEW
        )

    async def record_view(session, company_id, user_id, invite_id, via=None):
        await record(
            session,
            company_id,
            user_id,
            AuditAction.RESULTS_VIEWED,
            invite_id,
            via,
            TargetKind.CANDIDATE,
        )

    monkeypatch.setattr(audit, "record", record)
    monkeypatch.setattr(audit, "record_interview", record_interview)
    monkeypatch.setattr(audit, "record_view", record_view)

    return events


@pytest.fixture(autouse=True)
def stored_candidates(monkeypatch):
    """Candidates in memory (tests.unit.fake_candidates), emptied for each test."""
    fake_candidates.ROWS.clear()
    fake_candidates.SAVED.clear()

    for name in ("get", "counts", "any_finished", "unscored", "save_results", "for_report"):
        monkeypatch.setattr(candidates, name, getattr(fake_candidates, name))

    return fake_candidates


@pytest.fixture(autouse=True)
def nothing_cached(monkeypatch):
    """Library's answers kept in memory (services/set_cache.py) start empty for each test."""
    monkeypatch.setattr(memory_cache, "_entries", {})


@pytest.fixture(autouse=True)
def limit_hits(monkeypatch):
    """The limit hits recorded (the data of each limit.hit event), never published."""
    hits = []

    async def publish(event_type, data, attempts, timeout):
        hits.append(data)

    monkeypatch.setattr(limits, "publish_retried", publish)

    return hits


@pytest.fixture
def superadmin(monkeypatch):
    """Signs in `email`; ann@example.com is the only superadmin."""
    monkeypatch.setenv("SUPERADMIN_EMAILS", "ann@example.com")

    def sign_in(email):
        app.dependency_overrides[current_user] = lambda: User(
            uid=email,
            email=email,
            email_verified=True,
            sign_in_provider="google.com",
        )

    yield sign_in
    app.dependency_overrides.clear()
