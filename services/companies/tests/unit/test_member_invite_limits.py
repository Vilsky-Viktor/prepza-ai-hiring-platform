import uuid
from datetime import UTC, datetime

import pytest

from app.constants.roles import TOO_MANY_PENDING
from app.integrations import billing
from app.models.companies import Member
from app.routers import members as members_router
from app.storage import audit, companies, members
from tests.unit.fake_redis import FakeRedis
from tests.unit.test_members import COMPANY_ID, sign_in
from tests.unit.test_team_members import team  # noqa: F401

URL = f"/members?company_id={COMPANY_ID}"
TOO_MANY_REQUESTS = "Too many requests. Try again later."


@pytest.fixture
def limits(monkeypatch):
    """The members routes' Redis, with no limit edited unless a test puts one in `limits`; the
    action log isn't what these tests check."""
    redis = FakeRedis()

    async def nothing(*args, **kwargs):
        return None

    monkeypatch.setattr(members_router, "get_redis", lambda: redis)
    monkeypatch.setattr(audit, "record", nothing)

    return redis


def pending(listed, count):
    """`count` more invites waiting, besides the team's own (Cid's)."""
    listed.extend(
        Member(
            id=uuid.uuid4(),
            invited_email=f"waiting{index}@example.com",
            role="viewer",
            created_at=datetime.now(UTC),
        )
        for index in range(count)
    )


@pytest.mark.parametrize("edited", [None, 5])
def test_a_company_holds_a_limited_number_of_pending_invites(
    client,
    team,  # noqa: F811
    limits,
    limit_hits,
    edited,
):
    listed, added, _ = team
    most = edited or 20

    if edited:
        limits.limits["MAX_PENDING_INVITES"] = str(edited)

    # Cid's invite waits already: one fewer than the most lets one more in.
    pending(listed, most - 2)
    sign_in("ann@example.com", uid="ann")
    allowed = client.post(URL, json={"email": "new@example.com"})
    listed.append(Member(id=uuid.uuid4(), invited_email="new@example.com", role="admin"))
    refused = client.post(URL, json={"email": "one-more@example.com"})

    assert allowed.status_code == 201
    assert refused.status_code == 409
    assert refused.json() == {"detail": TOO_MANY_PENDING}
    assert added == [("new@example.com", "admin")]
    assert [(hit["limit"], hit["company_id"], hit["user_id"]) for hit in limit_hits] == [
        ("MAX_PENDING_INVITES", str(COMPANY_ID), "ann")
    ]


@pytest.mark.parametrize("edited", [None, 2])
def test_a_company_that_never_paid_sends_a_limited_number_of_invites_a_day(
    client,
    team,  # noqa: F811
    limits,
    limit_hits,
    monkeypatch,
    edited,
):
    _, added, _ = team
    most = edited or 10

    if edited:
        limits.limits["MEMBER_INVITES_PER_UNPAID_DAY"] = str(edited)

    async def unpaid(_company_id):
        return False

    monkeypatch.setattr(billing, "company_paid", unpaid)
    sign_in("ann@example.com", uid="ann")

    for index in range(most):
        assert client.post(URL, json={"email": f"m{index}@example.com"}).status_code == 201

    refused = client.post(URL, json={"email": "one-more@example.com"})

    assert refused.status_code == 429
    assert refused.json() == {"detail": TOO_MANY_REQUESTS}
    assert limits.counts[f"rate:member-invites:{COMPANY_ID}"] == most + 1
    assert len(added) == most
    assert [(hit["limit"], hit["company_id"], hit["user_id"]) for hit in limit_hits] == [
        ("MEMBER_INVITES_PER_UNPAID_DAY", str(COMPANY_ID), "ann")
    ]


@pytest.mark.parametrize(("edited", "most"), [(None, 3), (5, 5)])
def test_nobody_becomes_owner_of_more_companies_than_one_person_may(
    client,
    team,  # noqa: F811
    limits,
    limit_hits,
    monkeypatch,
    edited,
    most,
):
    (_, bob, _), _, _ = team
    made = []
    owned = {"bob": most}

    if edited:
        limits.limits["MAX_OWNED_COMPANIES"] = str(edited)

    async def transfer(company, owner, member, most=None):
        made.append(member.user_id)

        return True

    async def owned_count(user_id):
        return owned[user_id]

    monkeypatch.setattr(members, "transfer_ownership", transfer)
    monkeypatch.setattr(companies, "owned_count", owned_count)
    sign_in("ann@example.com", uid="ann")
    refused = client.post(f"/members/{bob.id}/owner?company_id={COMPANY_ID}")
    owned["bob"] = most - 1
    allowed = client.post(f"/members/{bob.id}/owner?company_id={COMPANY_ID}")

    assert refused.status_code == 409
    assert refused.json() == {
        "detail": f"They already own as many companies as one person may: {most}."
    }
    assert allowed.status_code == 204
    assert made == ["bob"]
    # The refusal is the new owner's: theirs is the limit.
    assert [(hit["limit"], hit["company_id"], hit["user_id"]) for hit in limit_hits] == [
        ("MAX_OWNED_COMPANIES", str(COMPANY_ID), "bob")
    ]
