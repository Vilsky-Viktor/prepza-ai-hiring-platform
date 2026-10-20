"""The admin zone's patterns tab (routers/superadmin_patterns.py): superadmins list the patterns
of a status and approve or dismiss proposed ones; anyone else gets "not found". Storage is in
memory here; tests/integration/test_patterns.py covers the database."""

import logging
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from prepza_common.auth import current_user
from prepza_common.user import User

from app.constants.patterns import PatternStatus
from app.main import app
from app.storage import patterns

SEEN = datetime(2026, 10, 12, 5, tzinfo=UTC)


def pattern(status=PatternStatus.PROPOSED, text="Two options say the same thing."):
    return SimpleNamespace(
        id=uuid.uuid4(),
        text=text,
        flag="weak_options",
        question_count=4,
        first_seen=SEEN,
        last_seen=SEEN,
        status=status,
        reviewed_by=None,
        reviewed_at=None,
    )


@pytest.fixture
def stored(monkeypatch):
    rows = [pattern(), pattern(PatternStatus.APPROVED, "The scenario leaves out a detail.")]

    async def by_status(status, offset, limit):
        return [row for row in rows if row.status == status][offset : offset + limit]

    async def review(pattern_id, status, reviewed_by):
        found = [row for row in rows if row.id == pattern_id]

        if not found or found[0].status != PatternStatus.PROPOSED:
            return False

        found[0].status, found[0].reviewed_by = status, reviewed_by

        return True

    monkeypatch.setattr(patterns, "by_status", by_status)
    monkeypatch.setattr(patterns, "review", review)

    return rows


@pytest.fixture
def signed_in(monkeypatch):
    """Ann is the only superadmin."""
    monkeypatch.setenv("SUPERADMIN_EMAILS", "ann@example.com")

    def sign_in(email):
        app.dependency_overrides[current_user] = lambda: User(
            uid=email.split("@")[0],
            email=email,
            email_verified=True,
            sign_in_provider="google.com",
        )

    yield sign_in

    app.dependency_overrides.clear()


def test_a_superadmin_sees_the_proposed_patterns_by_default(client, stored, signed_in):
    signed_in("ann@example.com")

    response = client.get("/superadmin/patterns")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": str(stored[0].id),
            "text": "Two options say the same thing.",
            "flag": "weak_options",
            "question_count": 4,
            "first_seen": "2026-10-12T05:00:00Z",
            "last_seen": "2026-10-12T05:00:00Z",
            "status": "proposed",
            "reviewed_at": None,
        }
    ]


def test_the_list_shows_the_patterns_of_the_status_asked_for(client, stored, signed_in):
    signed_in("ann@example.com")

    approved = client.get("/superadmin/patterns", params={"status": "approved"}).json()

    assert [row["id"] for row in approved] == [str(stored[1].id)]
    assert client.get("/superadmin/patterns", params={"status": "dismissed"}).json() == []
    assert client.get("/superadmin/patterns", params={"status": "other"}).status_code == 422


@pytest.mark.parametrize(
    "action, status", [("approve", PatternStatus.APPROVED), ("dismiss", PatternStatus.DISMISSED)]
)
def test_a_superadmin_approves_or_dismisses_a_proposed_pattern(
    client, stored, signed_in, caplog, action, status
):
    signed_in("ann@example.com")
    caplog.set_level(logging.INFO)

    response = client.post(f"/superadmin/patterns/{stored[0].id}/{action}")

    assert response.status_code == 204
    assert (stored[0].status, stored[0].reviewed_by) == (status, "ann")
    # Who reviewed it is kept with it and in the logs.
    assert f"Quality pattern {stored[0].id} {status} by superadmin ann" in caplog.messages
    assert client.get("/superadmin/patterns").json() == []


@pytest.mark.parametrize("action", ["approve", "dismiss"])
def test_a_pattern_reviewed_already_is_refused(client, stored, signed_in, action):
    signed_in("ann@example.com")

    refused = client.post(f"/superadmin/patterns/{stored[1].id}/{action}")

    assert refused.status_code == 409
    assert refused.json()["detail"] == "This pattern was already reviewed"
    assert stored[1].status == PatternStatus.APPROVED


def test_a_pattern_that_doesnt_exist_is_refused_the_same_way(client, stored, signed_in):
    signed_in("ann@example.com")

    refused = client.post(f"/superadmin/patterns/{uuid.uuid4()}/approve")

    assert refused.status_code == 409
    assert refused.json()["detail"] == "This pattern was already reviewed"


@pytest.mark.parametrize(
    "method, path",
    [
        ("get", "/superadmin/patterns"),
        ("post", "/superadmin/patterns/{id}/approve"),
        ("post", "/superadmin/patterns/{id}/dismiss"),
    ],
)
def test_anyone_else_gets_not_found(client, stored, signed_in, method, path):
    signed_in("eve@example.com")

    response = getattr(client, method)(path.format(id=stored[0].id))

    assert response.status_code == 404
    assert stored[0].status == PatternStatus.PROPOSED
