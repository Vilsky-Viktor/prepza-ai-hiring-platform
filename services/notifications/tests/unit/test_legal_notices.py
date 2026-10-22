import asyncio
from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace

import pytest
from prepza_common.auth import current_user
from prepza_common.user import User

from app.constants.legal_notices import ALREADY_ASKED, TOO_LATE
from app.main import app
from app.services import audiences, bulk, bulk_content, legal_notices
from app.storage import bulk_recipients, bulk_sends, notifications

TODAY = datetime.now(UTC).date()
LATER = (TODAY + timedelta(days=20)).isoformat()
SOON = (TODAY + timedelta(days=3)).isoformat()


@pytest.fixture
def notices(monkeypatch):
    """The versions, the sends, the recipients and the bell, faked."""
    state = SimpleNamespace(sends={}, prepared={}, bell=[], announced=[])
    monkeypatch.setattr(
        legal_notices,
        "LEGAL_VERSIONS",
        {"terms": LATER, "privacy": SOON, "dpa": TODAY.isoformat()},
    )

    async def start(kind, about, asked_by):
        if (kind, about) in state.sends:
            return None

        state.sends[(kind, about)] = SimpleNamespace(
            id=f"{kind}-{about}", kind=kind, about=about, prepared_after=None, finished_at=None
        )

        return state.sends[(kind, about)].id

    async def of_kinds(kinds):
        return [send for send in state.sends.values() if send.kind in kinds]

    async def get(kind, about):
        return state.sends.get((kind, about))

    async def save_page(send_id, after, last, user_ids, done):
        state.prepared[send_id] = user_ids

        return True

    async def is_recipient(send_id, user_id):
        return user_id in state.prepared.get(send_id, [])

    async def user_ids(after, setting=None):
        return ["ann", "bob", "guest-1"]

    async def member_ids(after, editors_only):
        assert editors_only

        return ["ann"]

    async def add(event_id, event):
        if event_id in [key for key, _ in state.bell]:
            return False

        state.bell.append((event_id, event))

        return True

    async def announce(recipient, recipient_id):
        state.announced.append((recipient, recipient_id))

    monkeypatch.setattr(bulk_sends, "start", start)
    monkeypatch.setattr(bulk_sends, "of_kinds", of_kinds)
    monkeypatch.setattr(bulk_sends, "get", get)
    monkeypatch.setattr(bulk_sends, "save_page", save_page)
    monkeypatch.setattr(bulk_recipients, "is_recipient", is_recipient)
    monkeypatch.setattr(audiences.library, "user_ids", user_ids)
    monkeypatch.setattr(audiences.companies, "member_ids", member_ids)
    monkeypatch.setattr(notifications, "add", add)
    monkeypatch.setattr(bulk_content, "announce", announce)

    return state


def states():
    return {item["document"]: item["state"] for item in asyncio.run(legal_notices.states())}


def test_a_notice_is_asked_for_once_and_at_least_14_days_ahead(notices):
    assert states() == {"terms": "sendable", "privacy": "too_late", "dpa": "in_force"}

    asyncio.run(legal_notices.ask("terms", "sam"))

    with pytest.raises(Exception) as again:
        asyncio.run(legal_notices.ask("terms", "sam"))

    with pytest.raises(Exception) as soon:
        asyncio.run(legal_notices.ask("privacy", "sam"))

    assert (again.value.detail, soon.value.detail) == (ALREADY_ASKED, TOO_LATE)
    assert states()["terms"] == "sending"

    notices.sends[("legal_terms", LATER)].finished_at = datetime.now(UTC)

    assert states()["terms"] == "sent"


def test_the_terms_go_to_every_account_once_and_in_everyones_bell(notices):
    asyncio.run(legal_notices.ask("terms", "sam"))

    assert notices.prepared == {f"legal_terms-{LATER}": ["ann", "bob"]}
    [(_, event)] = notices.bell
    assert (event["recipient"], event["kind"], event["link"], event["data"]) == (
        "all",
        "legal_terms",
        "/terms",
        {"date": LATER},
    )
    assert notices.announced == [("all", "everyone")]

    # Working them out again (a run after a failed start) adds nothing to the bell.
    send = notices.sends[("legal_terms", LATER)]
    asyncio.run(bulk.prepare(send, until=0))

    assert len(notices.bell) == 1


def test_the_dpa_goes_to_owners_and_admins_each_in_their_own_bell(notices):
    legal_notices.LEGAL_VERSIONS["dpa"] = LATER
    asyncio.run(legal_notices.ask("dpa", "sam"))

    assert notices.prepared == {f"legal_dpa-{LATER}": ["ann"]}
    assert [(event["recipient"], event["recipient_id"]) for _, event in notices.bell] == [
        ("user", "ann")
    ]


def test_the_banner_shows_changes_noticed_until_they_apply_to_whom_they_concern(notices):
    legal_notices.LEGAL_VERSIONS["dpa"] = LATER
    asyncio.run(legal_notices.ask("terms", "sam"))
    asyncio.run(legal_notices.ask("dpa", "sam"))

    assert asyncio.run(legal_notices.upcoming("ann")) == [
        {"document": "terms", "version": LATER},
        {"document": "dpa", "version": LATER},
    ]
    assert asyncio.run(legal_notices.upcoming("bob")) == [{"document": "terms", "version": LATER}]

    # Once it applies, no banner.
    legal_notices.LEGAL_VERSIONS["terms"] = TODAY.isoformat()
    notices.sends[("legal_terms", TODAY.isoformat())] = SimpleNamespace(
        id="t", kind="legal_terms", about=TODAY.isoformat(), finished_at=None
    )

    assert asyncio.run(legal_notices.upcoming("bob")) == []


def test_only_a_superadmin_sees_and_asks_for_notices(client, notices, monkeypatch):
    monkeypatch.setenv("SUPERADMIN_EMAILS", "sam@prepza.dev")
    app.dependency_overrides[current_user] = lambda: User(
        uid="ann",
        email="ann@example.com",
        email_verified=True,
        sign_in_provider="google.com",
    )

    assert client.get("/superadmin/legal-notices").status_code == 404

    app.dependency_overrides[current_user] = lambda: User(
        uid="sam",
        email="sam@prepza.dev",
        email_verified=True,
        sign_in_provider="google.com",
    )

    assert client.post("/superadmin/legal-notices/terms").status_code == 204
    assert client.post("/superadmin/legal-notices/privacy").json()["detail"] == TOO_LATE
    assert client.get("/superadmin/legal-notices").json()[0] == {
        "document": "terms",
        "version": LATER,
        "state": "sending",
        "audience": "everyone",
    }

    app.dependency_overrides.clear()


def test_no_notice_lines_up_with_a_day_past(notices):
    assert legal_notices.earliest_version(date(2026, 10, 14)) == "2026-10-28"
