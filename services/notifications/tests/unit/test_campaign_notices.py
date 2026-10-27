import asyncio
import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from prepza_common.auth.auth import current_user
from prepza_common.auth.user import User

from app.constants.campaigns import CHANGED, NOT_ACKNOWLEDGED
from app.main import app
from app.services import campaign_sends
from app.storage import campaigns as campaigns_store

TEXTS = {"en": {"subject": "Planned downtime", "text": "Down on Sunday.", "button": None}}


@pytest.fixture
def sending(monkeypatch):
    """A draft notice; what was asked of the day's limit and the sent marker."""
    state = SimpleNamespace(kind="notices", marked=[], hits=[], outcome=uuid.uuid4())

    async def get(campaign_id):
        return SimpleNamespace(kind=state.kind), TEXTS

    async def mark_sent(campaign_id, kind, user_id, per_day):
        state.marked.append((kind, per_day))

        return state.outcome

    async def limit(redis, name):
        state.limit = name

        return 1

    async def nothing(*args, **kwargs):
        return None

    async def record_hit(name, **who):
        state.hits.append(name)

    monkeypatch.setattr(campaigns_store, "get", get)
    monkeypatch.setattr(campaigns_store, "mark_sent", mark_sent)
    monkeypatch.setattr(campaign_sends, "limit", limit)
    monkeypatch.setattr(campaign_sends, "get_redis", lambda: None)
    monkeypatch.setattr(campaign_sends, "record_hit", record_hit)
    monkeypatch.setattr(campaign_sends, "prepare_now", nothing)
    monkeypatch.setattr(campaign_sends, "get", nothing)

    return state


def test_a_notice_is_sent_only_once_confirmed_as_one_under_its_own_day_limit(sending):
    with pytest.raises(HTTPException) as refused:
        asyncio.run(campaign_sends.send(uuid.uuid4(), "sam", acknowledged=False))

    assert (refused.value.status_code, refused.value.detail) == (422, NOT_ACKNOWLEDGED)
    assert sending.marked == []

    asyncio.run(campaign_sends.send(uuid.uuid4(), "sam", acknowledged=True))

    assert sending.marked == [("notices", 1)] and sending.limit == "NOTICES_PER_DAY"


def test_a_campaign_whose_kind_changed_before_it_was_marked_sent_is_refused(sending):
    sending.outcome = CHANGED

    with pytest.raises(HTTPException) as refused:
        asyncio.run(campaign_sends.send(uuid.uuid4(), "sam", acknowledged=True))

    assert (refused.value.status_code, refused.value.detail) == (409, CHANGED)


@pytest.fixture
def superadmin(monkeypatch):
    monkeypatch.setenv("SUPERADMIN_EMAILS", "sam@prepza.dev")
    app.dependency_overrides[current_user] = lambda: User(
        uid="sam", email="sam@prepza.dev", email_verified=True, sign_in_provider="google.com"
    )


def test_the_dialogs_count_is_the_services_and_a_send_passes_the_confirmation(
    client, superadmin, monkeypatch
):
    counted, sent = [], []

    async def reachable(chosen):
        counted.append(chosen)

        return 7

    async def send(campaign_id, user_id, acknowledged):
        sent.append(acknowledged)

        raise HTTPException(422, NOT_ACKNOWLEDGED)

    monkeypatch.setattr(campaign_sends, "reachable", reachable)
    monkeypatch.setattr(campaign_sends, "send", send)
    body = {"kind": "notices", "groups": ["learners"], "editors_only": False, "company_ids": []}

    assert client.post("/superadmin/campaigns/recipients", json=body).json() == {"count": 7}
    assert counted[0].groups == ["learners"]
    client.post(f"/superadmin/campaigns/{uuid.uuid4()}/send", json={"acknowledged": True})
    client.post(f"/superadmin/campaigns/{uuid.uuid4()}/send")
    assert sent == [True, False]
