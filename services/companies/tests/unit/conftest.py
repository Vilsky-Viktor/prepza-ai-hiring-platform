import pytest
from prepza_common import limits, memory_cache
from prepza_common.audit_actions import AuditAction, TargetKind
from prepza_common.auth import current_user
from prepza_common.user import User

from app.integrations import billing
from app.main import app
from app.service_auth import REQUEST_VIA
from app.storage import accounts, audit, candidates, companies, invites
from tests.unit import fake_candidates


@pytest.fixture(autouse=True)
def no_billing_calls(monkeypatch):
    """Billing is another service; tests that care about its calls replace these."""

    async def nothing(*args, **kwargs):
        return None

    async def no_invites(user_id, email):
        return []

    for name in ("delete_company", "release_candidate", "charge_candidate", "welcome_company"):
        monkeypatch.setattr(billing, name, nothing)

    async def none_unfinished(interview_id, after, size):
        return []

    monkeypatch.setattr(accounts, "unfinished_invites", no_invites)
    monkeypatch.setattr(invites, "unfinished", none_unfinished)


@pytest.fixture(autouse=True)
def no_company_by_default(monkeypatch):
    """Looking a company up finds none unless a test stores one (unit tests have no database)."""

    async def none(company_id):
        return None

    monkeypatch.setattr(companies, "get", none)


@pytest.fixture(autouse=True)
def audited(monkeypatch):
    """The action log, in memory: (company id, user id, action, target id, target kind) as
    recorded, with via after them when it's set (by the caller or the request). An interview's actions (record_interview) and
    results views (record_view) land here too."""
    events = []

    async def record(company_id, user_id, action, target_id=None, via=None, target_kind=None, **_):
        # As the real one: what the request came through, unless the caller says.
        via = via or REQUEST_VIA.get()
        events.append(
            (company_id, user_id, action, target_id, target_kind, *([via] if via else []))
        )

    async def record_interview(interview, user_id, action, via=None):
        await record(interview.company_id, user_id, action, interview.id, via, TargetKind.INTERVIEW)

    async def record_view(company_id, user_id, invite_id, via=None):
        await record(
            company_id, user_id, AuditAction.RESULTS_VIEWED, invite_id, via, TargetKind.CANDIDATE
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
