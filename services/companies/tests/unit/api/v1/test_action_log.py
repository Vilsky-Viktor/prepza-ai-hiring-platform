"""The owner's action log route: who may read it, its filters, and its rows."""

import asyncio
import uuid
from datetime import UTC, datetime

import pytest
from prepza_common.auth.auth import current_user
from prepza_common.auth.key_actor import key_actor
from prepza_common.auth.user import User
from prepza_common.events.audit_actions import AUDIT_RECORDED, AuditAction, AuditGroup, TargetKind

from companies.handlers import dispatch
from companies.integrations import api_keys
from companies.main import app
from companies.models.audit import AuditEvent
from companies.models.companies import Company, Member
from companies.repositories import action_names, audit, companies

COMPANY_ID = uuid.uuid4()
BOB_ID = uuid.uuid4()
INVITED_ID = uuid.uuid4()
URL = f"/companies/{COMPANY_ID}/actions"
NOW = datetime(2026, 10, 16, 9, 30, tzinfo=UTC)
# Two API keys that invited candidates: one over the API, renamed since, one over MCP, deleted.
RENAMED_KEY, DELETED_KEY = uuid.uuid4(), uuid.uuid4()


def sign_in(uid):
    app.dependency_overrides[current_user] = lambda: User(
        uid=uid, email=f"{uid}@example.com", email_verified=True
    )


@pytest.fixture
def log(monkeypatch):
    """Acme: Ann its owner, Bob an admin, Vic a viewer, and Cid invited but not joined. Its log
    has Bob's results view of a candidate, Ann's change of an API key's permissions, an action
    by a member who left, and invites by two API keys (one renamed, one deleted). The filters
    each list asked with are kept, and the keys whose names were asked for."""
    acme = Company(id=COMPANY_ID, name="Acme", created_at=NOW)
    acme.members = [
        Member(company_id=COMPANY_ID, user_id="ann", invited_email="ann@x.com", role="owner"),
        Member(
            id=BOB_ID, company_id=COMPANY_ID, user_id="bob", invited_email="bob@x.com", role="admin"
        ),
        Member(company_id=COMPANY_ID, user_id="vic", invited_email="vic@x.com", role="viewer"),
        Member(id=INVITED_ID, company_id=COMPANY_ID, invited_email="cid@x.com", role="admin"),
    ]
    candidate_id = uuid.uuid4()
    gone_id = uuid.uuid4()
    rows = [
        AuditEvent(
            id=uuid.uuid4(),
            user_id="bob",
            action=AuditAction.RESULTS_VIEWED,
            group=AuditGroup.CANDIDATES,
            target_kind=TargetKind.CANDIDATE,
            target_id=candidate_id,
            via="assistant",
            created_at=NOW,
        ),
        AuditEvent(
            id=uuid.uuid4(),
            user_id="ann",
            action=AuditAction.API_KEY_PERMISSIONS_CHANGED,
            group=AuditGroup.INTEGRATIONS,
            target_kind=TargetKind.API_KEY,
            target_id=uuid.uuid4(),
            target_label="Zapier",
            removed=["candidates:delete"],
            created_at=NOW,
        ),
        AuditEvent(
            id=uuid.uuid4(),
            user_id="left",
            action=AuditAction.CANDIDATE_DELETED,
            group=AuditGroup.CANDIDATES,
            target_kind=TargetKind.CANDIDATE,
            target_id=gone_id,
            created_at=NOW,
        ),
        *[
            AuditEvent(
                id=uuid.uuid4(),
                user_id=key_actor(key_id),
                action=AuditAction.CANDIDATE_INVITED,
                group=AuditGroup.CANDIDATES,
                target_kind=TargetKind.CANDIDATE,
                target_id=candidate_id,
                via=via,
                key_id=key_id,
                created_at=NOW,
            )
            for key_id, via in ((RENAMED_KEY, "api"), (DELETED_KEY, "mcp"))
        ],
    ]
    asked = []

    async def get(session, _id):
        return acme

    async def list_for_company(session, company_id, offset, limit, *filters):
        asked.append((offset, limit, *filters))

        return rows

    async def member_emails(session, company_id, user_ids):
        return {"ann": "ann@x.com", "bob": "bob@x.com"}

    async def target_names(session, company_id, ids):
        return {candidate_id: "cara@example.com"}

    async def key_names(company_id, key_ids):
        asked.append(("keys", company_id, sorted(key_ids)))

        # The api service: the renamed key by its name now; the deleted one is gone.
        return {str(RENAMED_KEY): "Zapier v2"}

    monkeypatch.setattr(companies, "get", get)
    monkeypatch.setattr(audit, "list_for_company", list_for_company)
    monkeypatch.setattr(action_names, "member_emails", member_emails)
    monkeypatch.setattr(action_names, "target_names", target_names)
    monkeypatch.setattr(api_keys, "names", key_names)

    yield asked

    app.dependency_overrides.clear()


def test_the_owner_reads_who_did_what_and_about_what(client, log):
    sign_in("ann")
    response = client.get(URL)

    assert response.status_code == 200
    assert [
        (row["action"], row["group"], row["user_email"], row["target"], row["via"], row["removed"])
        for row in response.json()[:3]
    ] == [
        ("results_viewed", "candidates", "bob@x.com", "cara@example.com", "assistant", None),
        (
            "api_key_permissions_changed",
            "integrations",
            "ann@x.com",
            "Zapier",
            None,
            ["candidates:delete"],
        ),
        # A former member and a deleted candidate: nobody's email is kept.
        ("candidate_deleted", "candidates", None, None, None, None),
    ]


def test_an_api_key_is_its_own_author_named_as_it_is_now(client, log):
    """Never a person: the key by its name now (None once deleted), and the way it came."""
    sign_in("ann")
    rows = client.get(URL).json()

    assert [(row["user_email"], row["key_id"], row["key_name"], row["via"]) for row in rows] == [
        ("bob@x.com", None, None, "assistant"),
        ("ann@x.com", None, None, None),
        (None, None, None, None),
        (None, str(RENAMED_KEY), "Zapier v2", "api"),
        (None, str(DELETED_KEY), None, "mcp"),
    ]
    # Their names asked for at once.
    assert log[-1] == ("keys", COMPANY_ID, sorted([RENAMED_KEY, DELETED_KEY]))


@pytest.mark.parametrize(("uid", "code"), [("bob", 403), ("vic", 403), ("mallory", 404)])
def test_admins_viewers_and_others_are_refused(client, log, uid, code):
    sign_in(uid)

    assert client.get(URL).status_code == code
    assert client.get(f"/companies/{COMPANY_ID}/audit").status_code == code
    assert log == []


def test_the_filters_go_to_the_log_with_a_member_as_their_user(client, log):
    sign_in("ann")
    start, end = "2026-10-01T00:00:00Z", "2026-10-17T00:00:00Z"
    params = {"member_id": str(BOB_ID), "group": "candidates", "from": start, "to": end}

    assert client.get(URL, params={**params, "offset": 20, "limit": 10}).status_code == 200
    assert client.get(URL).status_code == 200
    assert log == [
        (
            20,
            10,
            "bob",
            AuditGroup.CANDIDATES,
            datetime(2026, 10, 1, tzinfo=UTC),
            datetime(2026, 10, 17, tzinfo=UTC),
        ),
        ("keys", COMPANY_ID, sorted([RENAMED_KEY, DELETED_KEY])),
        (0, log[2][1], None, None, None, None),
        ("keys", COMPANY_ID, sorted([RENAMED_KEY, DELETED_KEY])),
    ]


@pytest.mark.parametrize("member_id", [INVITED_ID, uuid.uuid4()])
def test_a_member_who_hasnt_joined_or_isnt_there_is_not_found(client, log, member_id):
    sign_in("ann")

    assert client.get(URL, params={"member_id": str(member_id)}).status_code == 404
    assert log == []


def test_an_unknown_group_is_refused(client, log):
    sign_in("ann")

    assert client.get(URL, params={"group": "everything"}).status_code == 422


def test_only_another_services_action_is_stored_at_the_time_it_happened(monkeypatch):
    stored = []

    async def store_event(session, event_id, data, at):
        stored.append((event_id, data["action"], at))

    monkeypatch.setattr(audit, "store_event", store_event)
    data = {"company_id": str(COMPANY_ID), "user_id": "ann", "action": "top_up_paid"}

    asyncio.run(dispatch.handle(AUDIT_RECORDED, data, "e1", NOW))
    asyncio.run(dispatch.handle("candidate.finished", data, "e2", NOW))

    assert stored == [("e1", "top_up_paid", NOW)]
