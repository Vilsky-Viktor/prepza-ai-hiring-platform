import uuid
from types import SimpleNamespace

import pytest
from prepza_common import ai_cap
from prepza_common.ai_constants import AI_PAUSED_TODAY, LIMIT_HIT, MICRO
from prepza_common.auth import current_user
from prepza_common.limit_list import LIMITS
from prepza_common.user import User

from app.main import app
from app.models.generation import Generation
from app.routers import internal
from app.storage import generations
from tests.unit.test_internal_generations import headers

COMPANY_ID = uuid.uuid4()
SET_ID = uuid.uuid4()


@pytest.fixture
def started(monkeypatch):
    """Generations and regenerated questions that got past the checks."""
    calls = []

    async def create(owner_uid, text, company_id=None, language="en", **kwargs):
        calls.append(("generation", owner_uid))

        return Generation(
            id=uuid.uuid4(),
            owner_uid=owner_uid,
            text=text,
            kind=kwargs.get("kind", "interview"),
            company_id=company_id,
            status="queued",
            language=language,
        )

    async def context(question_id):
        return SimpleNamespace(set_id=SET_ID, kind="interview", owner_id=str(COMPANY_ID))

    async def regenerate(question_id, found):
        calls.append(("regeneration", question_id))

        return {"id": str(question_id), "text": "New question?"}

    monkeypatch.setattr(generations, "create", create)
    monkeypatch.setattr(internal.library, "get_question_context", context)
    monkeypatch.setattr(internal, "regenerate", regenerate)

    return calls


def spent(redis, usd):
    """Today's unpaid AI spend so far."""
    redis.counts[ai_cap.today_key()] = round(usd * MICRO)


def generate(client, paid):
    return client.post(
        "/internal/generations",
        json={
            "text": "Accountant",
            "company_id": str(COMPANY_ID),
            "owner_uid": "bob",
            "paid": paid,
        },
        headers=headers(),
    )


def regenerate(client, paid):
    return client.post(
        f"/internal/questions/{uuid.uuid4()}/regenerate",
        json={"user_id": "bob", "set_id": str(SET_ID), "paid": paid},
        headers=headers(),
    )


@pytest.mark.parametrize("call", [generate, regenerate])
def test_an_unpaid_companys_ai_stops_once_the_unpaid_spend_reaches_the_default_cap(
    client, redis, events, started, call
):
    spent(redis, LIMITS["AI_SPEND_UNPAID_DAY"].default)

    refused = call(client, paid=False)

    assert refused.status_code == 503
    assert refused.json()["detail"] == AI_PAUSED_TODAY
    assert started == []
    [(kind, hit)] = events
    assert kind == LIMIT_HIT
    assert (hit["limit"], hit["company_id"], hit["user_id"]) == (
        "AI_SPEND_UNPAID_DAY",
        str(COMPANY_ID),
        "bob",
    )


@pytest.mark.parametrize("call", [generate, regenerate])
def test_a_paid_companys_ai_goes_on_past_the_cap(client, redis, started, call):
    spent(redis, LIMITS["AI_SPEND_UNPAID_DAY"].default)

    assert call(client, paid=True).status_code < 300
    assert len(started) == 1


def test_the_cap_is_its_edited_value(client, redis, started):
    redis.limits["AI_SPEND_UNPAID_DAY"] = "2"
    spent(redis, 1.99)

    assert generate(client, paid=False).status_code == 201

    spent(redis, 2)

    assert generate(client, paid=False).status_code == 503
    assert len(started) == 1


def test_prepzas_own_templates_arent_held_to_the_unpaid_cap(client, redis, started, monkeypatch):
    spent(redis, LIMITS["AI_SPEND_UNPAID_DAY"].default)
    monkeypatch.setenv("SUPERADMIN_EMAILS", "ann@example.com")
    app.dependency_overrides[current_user] = lambda: User(
        uid="ann",
        email="ann@example.com",
        email_verified=True,
        sign_in_provider="google.com",
    )

    try:
        response = client.post("/superadmin/templates", json={"text": "Senior accountant"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert started == [("generation", "ann")]
