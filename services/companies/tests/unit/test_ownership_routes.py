import pytest
from prepza_common.events.audit_actions import AuditAction, TargetKind

from app.constants.roles import ONLY_ADMINS_OWN
from app.routers import members as members_router
from app.storage import companies, members
from tests.unit import test_team_members
from tests.unit.test_members import COMPANY_ID, sign_in

# The team of test_team_members: Ann the owner, Bob a joined admin, Cid an invited one.
team = test_team_members.team


@pytest.fixture
def transfers(monkeypatch):
    """The transfers made, and how many companies each new owner already owns (none)."""
    made = []
    owned = {}

    async def transfer(company, owner, member, most=None):
        made.append((owner.user_id, member.user_id))

        return True

    async def owned_count(user_id):
        return owned.get(user_id, 0)

    monkeypatch.setattr(members, "transfer_ownership", transfer)
    monkeypatch.setattr(companies, "owned_count", owned_count)

    return made, owned


def owner_url(member):
    return f"/members/{member.id}/owner?company_id={COMPANY_ID}"


def test_the_owner_makes_a_joined_admin_the_owner(client, team, transfers, audited):
    (_, bob, _), _, _ = team
    made, _ = transfers
    sign_in("ann@example.com", uid="ann")

    assert client.post(owner_url(bob)).status_code == 204
    assert made == [("ann", "bob")]
    assert audited == [
        (COMPANY_ID, "ann", AuditAction.OWNERSHIP_TRANSFERRED, bob.id, TargetKind.MEMBER)
    ]


def test_only_a_joined_admin_owning_fewer_than_three_can_become_owner(
    client, team, transfers, audited
):
    (_, bob, cid), _, _ = team
    made, owned = transfers
    sign_in("ann@example.com", uid="ann")

    # A pending invite, and a viewer.
    pending = client.post(owner_url(cid))
    bob.role = "viewer"
    viewer = client.post(owner_url(bob))
    bob.role = "admin"
    owned["bob"] = 3
    full = client.post(owner_url(bob))

    assert [r.status_code for r in (pending, viewer, full)] == [409, 409, 409]
    assert pending.json()["detail"] == ONLY_ADMINS_OWN
    assert full.json()["detail"] == "They already own as many companies as one person may: 3."
    assert made == [] and audited == []


def test_only_the_owner_hands_the_company_on(client, team, transfers):
    (owner, _, _), _, _ = team
    sign_in("bob@example.com", uid="bob")

    assert client.post(owner_url(owner)).status_code == 403


def test_the_team_says_who_the_owner_can_make_owner(client, team):
    sign_in("ann@example.com", uid="ann")
    listed = client.get(f"/members?company_id={COMPANY_ID}").json()

    # Bob joined as an admin; Cid is only invited; Ann is the owner.
    assert {row["email"]: row["can_own"] for row in listed} == {
        "ann@example.com": False,
        "bob@example.com": True,
        "cid@example.com": False,
    }
    assert members_router.ONLY_ADMINS_OWN
