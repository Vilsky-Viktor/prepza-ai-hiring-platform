"""Actions recorded in the company's action log by routes that have no test of their own for it:
renaming an interview, its shareable link, and the automatic top-up."""

import uuid
from datetime import UTC, datetime

import pytest
from prepza_common.audit_actions import AuditAction, TargetKind
from prepza_common.auth import current_user
from prepza_common.user import User

from app.integrations import billing_prices, library
from app.main import app
from app.models.companies import Company, Member
from app.models.interviews import Interview
from app.routers import auto_top_ups as auto_top_ups_router
from app.routers import links as links_router
from app.storage import companies, interviews

COMPANY_ID = uuid.uuid4()
INTERVIEW_ID = uuid.uuid4()
OFF = {
    "offered": True,
    "on": False,
    "waiting": False,
    "product": None,
    "threshold": None,
    "products": ["pack_10"],
    "thresholds": [5],
    "currency": "USD",
    "prices": {"topup_50": 5000},
}


def sign_in(uid):
    app.dependency_overrides[current_user] = lambda: User(
        uid=uid, email=f"{uid}@example.com", email_verified=True
    )


@pytest.fixture(autouse=True)
def company(monkeypatch):
    """Acme, with Ann its owner and Vic a viewer, and its interview "Backend"; signed in as
    Ann. Its automatic top-up is off until it's turned on."""
    acme = Company(id=COMPANY_ID, name="Acme", created_at=datetime.now(UTC))
    acme.members = [
        Member(company_id=COMPANY_ID, user_id="ann", invited_email="ann@x.com", role="owner"),
        Member(company_id=COMPANY_ID, user_id="vic", invited_email="vic@x.com", role="viewer"),
    ]
    interview = Interview(
        id=INTERVIEW_ID, company_id=COMPANY_ID, title="Backend", set_id=uuid.uuid4()
    )
    top_up = dict(OFF)

    async def get_company(_id):
        return acme

    async def get_interview(_id):
        return interview

    async def nothing(*args, **kwargs):
        return None

    async def current(_company_id, country=None):
        return dict(top_up)

    async def turn_on(_company_id, body, buyer_id, country, language):
        top_up.update(on=True, **body)

        return dict(top_up)

    monkeypatch.setattr(companies, "get", get_company)
    monkeypatch.setattr(interviews, "get", get_interview)

    for module, name in (
        (library, "rename_set"),
        (interviews, "set_title"),
        (interviews, "set_link"),
        (links_router, "ready_for_invites"),
        (billing_prices, "turn_off_auto_top_up"),
        (auto_top_ups_router, "count_checkout_call"),
    ):
        monkeypatch.setattr(module, name, nothing)

    monkeypatch.setattr(billing_prices, "auto_top_up", current)
    monkeypatch.setattr(billing_prices, "turn_on_auto_top_up", turn_on)
    sign_in("ann")

    yield

    app.dependency_overrides.clear()


def interview_action(action):
    return (COMPANY_ID, "ann", action, INTERVIEW_ID, TargetKind.INTERVIEW)


def test_renaming_an_interview_is_recorded(client, audited):
    response = client.patch(f"/interviews/{INTERVIEW_ID}/title", json={"title": "Backend II"})

    assert response.status_code == 204
    assert audited == [interview_action(AuditAction.INTERVIEW_RENAMED)]


def test_turning_the_link_on_and_off_is_recorded(client, audited):
    url = f"/interviews/{INTERVIEW_ID}/link"

    assert client.put(url, json={"on": True}).status_code == 200
    assert client.put(url, json={"on": False}).status_code == 200
    assert audited == [
        interview_action(AuditAction.LINK_TURNED_ON),
        interview_action(AuditAction.LINK_TURNED_OFF),
    ]


def test_setting_up_changing_and_stopping_the_automatic_top_up_is_recorded(client, audited):
    url = f"/companies/{COMPANY_ID}/auto-top-up"
    body = {"product": "pack_10", "threshold": 5}

    assert client.put(url, json=body).status_code == 200
    assert client.put(url, json=body).status_code == 200
    assert client.delete(url).status_code == 204
    assert audited == [
        (COMPANY_ID, "ann", action, COMPANY_ID, TargetKind.COMPANY)
        for action in (
            AuditAction.AUTO_TOP_UP_SET,
            AuditAction.AUTO_TOP_UP_CHANGED,
            AuditAction.AUTO_TOP_UP_STOPPED,
        )
    ]


def test_turning_on_passes_the_interface_language_to_billing(client, audited, monkeypatch):
    """Billing names what each automatic charge buys in it."""
    languages = []

    async def turn_on(_company_id, body, buyer_id, country, language):
        languages.append(language)

        return {**OFF, **body}

    monkeypatch.setattr(billing_prices, "turn_on_auto_top_up", turn_on)
    url = f"/companies/{COMPANY_ID}/auto-top-up"
    body = {"product": "pack_10", "threshold": 5}

    client.put(url, json=body, headers={"Accept-Language": "pl-PL,pl;q=0.9"})
    client.put(url, json=body)

    assert languages == ["pl", "en"]


def test_a_viewer_changes_nothing_and_nothing_is_recorded(client, audited):
    sign_in("vic")

    assert (
        client.patch(f"/interviews/{INTERVIEW_ID}/title", json={"title": "Backend II"}).status_code
        == 403
    )
    assert client.put(f"/interviews/{INTERVIEW_ID}/link", json={"on": True}).status_code == 403
    assert client.delete(f"/companies/{COMPANY_ID}/auto-top-up").status_code == 403
    assert audited == []
