import uuid
from datetime import UTC, datetime

import pytest
from fastapi import HTTPException, status
from prepza_common.events.audit_actions import AuditAction, TargetKind

from companies.integrations import billing, billing_prices
from companies.models.companies import Company, Member
from companies.repositories import companies, members
from companies.services import members as members_router
from companies.services import outbox as outbox_service
from tests.unit.api.v1.test_members import (  # noqa: F401 (fixture)
    COMPANY_ID,
    clear_overrides,
    fake_flush,
    flushed,
    sign_in,
)

# What each invite's email was sent with, and the email limits' keys, in the `team` fixture.
senders = []
limited = []


async def fake_hit_emails(redis, uid, key, *limits):
    limited.append((uid, key))


@pytest.fixture
def team(monkeypatch):
    """Ann owns the company, Bob joined as an admin, Cid's invite is pending. Returns what was
    removed, added or given a new role, and whose auto top-up billing was asked to turn off."""
    company = Company(id=COMPANY_ID, name="Arcolabs", created_at=datetime.now(UTC))
    company.members = [
        Member(
            id=uuid.uuid4(),
            user_id=uid,
            invited_email=f"{name}@example.com",
            role=role,
            created_at=datetime.now(UTC),
        )
        for uid, name, role in (
            ("ann", "ann", "owner"),
            ("bob", "bob", "admin"),
            (None, "cid", "admin"),
        )
    ]
    removed = []
    turned_off = []
    senders.clear()

    async def fake_company(session, _company_id):
        return company

    async def fake_paid(_company_id):
        return True

    async def fake_remove(session, member_id):
        removed.append(member_id)

    async def fake_turn_off(company_id, buyer_id=None):
        turned_off.append(buyer_id)

    async def fake_list(session, company_id, offset, limit):
        return company.members

    async def fake_set_role(session, member_id, role):
        removed.append((member_id, role))

    async def fake_add(session, company_id, email, role, sender, most=None):
        removed.append((email, role))
        senders.append(sender)

        return Member(id=uuid.uuid4(), invited_email=email, role=role, created_at=datetime.now(UTC))

    monkeypatch.setattr(members, "set_role", fake_set_role)
    monkeypatch.setattr(members, "add", fake_add)
    monkeypatch.setattr(companies, "get", fake_company)
    monkeypatch.setattr(members, "remove", fake_remove)
    monkeypatch.setattr(members, "list_for_company", fake_list)
    monkeypatch.setattr(billing_prices, "turn_off_auto_top_up", fake_turn_off)
    monkeypatch.setattr(members_router, "hit_emails", fake_hit_emails)
    monkeypatch.setattr(outbox_service, "flush_quietly", fake_flush)
    # A paying company: the daily cap for unpaid ones doesn't count (test_member_invite_limits).
    monkeypatch.setattr(billing, "company_paid", fake_paid)

    return company.members, removed, turned_off


def remove_url(member):
    return f"/members/{member.id}?company_id={COMPANY_ID}"


def test_the_owner_removes_an_admin_and_their_card_stops_paying(client, team, audited):
    (_, bob, cid), removed, turned_off = team
    sign_in("ann@example.com", uid="ann")

    assert client.delete(remove_url(bob)).status_code == 204
    assert client.delete(remove_url(cid)).status_code == 204
    assert removed == [bob.id, cid.id]
    # A pending invite has no card to stop.
    assert turned_off == ["bob"]
    assert audited == [
        (COMPANY_ID, "ann", AuditAction.MEMBER_REMOVED, member.id, TargetKind.MEMBER)
        for member in (bob, cid)
    ]


def test_nobody_removes_the_owner_and_admins_remove_nobody(client, team, audited):
    (owner, _, cid), removed, _ = team
    sign_in("ann@example.com", uid="ann")

    assert client.delete(remove_url(owner)).status_code == 409

    sign_in("bob@example.com", uid="bob")

    assert client.delete(remove_url(cid)).status_code == 403
    assert removed == [] and audited == []


def test_the_list_says_which_rows_can_be_removed(client, team):
    sign_in("ann@example.com", uid="ann")
    owners_view = client.get(f"/members?company_id={COMPANY_ID}").json()
    sign_in("bob@example.com", uid="bob")
    admins_view = client.get(f"/members?company_id={COMPANY_ID}").json()

    assert [row["removable"] for row in owners_view] == [False, True, True]
    assert [row["removable"] for row in admins_view] == [False, False, False]


def role_url(member):
    return f"/members/{member.id}/role?company_id={COMPANY_ID}"


def test_the_owner_invites_a_viewer_and_an_admin_by_default(client, team, audited):
    _, changed, _ = team
    sign_in("ann@example.com", uid="ann")
    url = f"/members?company_id={COMPANY_ID}"

    viewer = client.post(url, json={"email": "dan@example.com", "role": "viewer"})
    admin = client.post(url, json={"email": "eve@example.com"})

    assert (viewer.status_code, viewer.json()["role"]) == (201, "viewer")
    assert (admin.status_code, admin.json()["role"]) == (201, "admin")
    assert changed == [("dan@example.com", "viewer"), ("eve@example.com", "admin")]
    assert audited == [
        (
            COMPANY_ID,
            "ann",
            AuditAction.MEMBER_INVITED,
            uuid.UUID(row.json()["id"]),
            TargetKind.MEMBER,
        )
        for row in (viewer, admin)
    ]
    # Nobody is invited as a second owner.
    assert client.post(url, json={"email": "fay@example.com", "role": "owner"}).status_code == 422


def test_an_invite_emails_the_member_from_the_owner_within_their_email_limits(client, team):
    _ = team
    limited.clear()
    flushed.clear()
    sign_in("ann@example.com", uid="ann")

    client.post(f"/members?company_id={COMPANY_ID}", json={"email": "Dan@example.com"})

    assert senders == [
        {
            "company": "Arcolabs",
            "company_id": str(COMPANY_ID),
            "logo_path": None,
            "inviter": "Bob",
            "language": "en",
        }
    ]
    assert limited == [("ann", f"member:{COMPANY_ID}:dan@example.com")]
    # Sent right away, not on the outbox's next run.
    assert flushed


def test_a_tagged_address_counts_as_its_inbox_but_is_invited_as_given(client, team):
    _, changed, _ = team
    limited.clear()
    sign_in("ann@example.com", uid="ann")

    client.post(f"/members?company_id={COMPANY_ID}", json={"email": "Dan+Team@example.com"})

    # name+tag@ reaches name@'s inbox, so the per-recipient limit counts them together.
    assert limited == [("ann", f"member:{COMPANY_ID}:dan@example.com")]
    assert changed[-1] == ("dan+team@example.com", "admin")


def test_an_owner_over_their_email_limits_invites_nobody(client, team, monkeypatch, audited):
    _, changed, _ = team

    async def over(*args):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many emails")

    monkeypatch.setattr(members_router, "hit_emails", over)
    sign_in("ann@example.com", uid="ann")

    response = client.post(f"/members?company_id={COMPANY_ID}", json={"email": "dan@example.com"})

    assert response.status_code == 429
    assert changed == [] and audited == []


def test_the_owner_makes_an_admin_a_viewer_and_their_card_stops_paying(client, team, audited):
    (_, bob, cid), changed, turned_off = team
    sign_in("ann@example.com", uid="ann")

    assert client.put(role_url(bob), json={"role": "viewer"}).status_code == 204
    assert client.put(role_url(cid), json={"role": "viewer"}).status_code == 204
    assert client.put(role_url(bob), json={"role": "admin"}).status_code == 204
    assert changed == [(bob.id, "viewer"), (cid.id, "viewer"), (bob.id, "admin")]
    assert turned_off == ["bob"]
    assert [event[2:] for event in audited] == [
        (AuditAction.MEMBER_ROLE_CHANGED, member.id, TargetKind.MEMBER)
        for member in (bob, cid, bob)
    ]


def test_only_the_owner_changes_roles_and_never_their_own(client, team, audited):
    (owner, _, cid), changed, _ = team
    sign_in("ann@example.com", uid="ann")

    assert client.put(role_url(owner), json={"role": "viewer"}).status_code == 409

    sign_in("bob@example.com", uid="bob")

    assert client.put(role_url(cid), json={"role": "viewer"}).status_code == 403
    assert changed == [] and audited == []
