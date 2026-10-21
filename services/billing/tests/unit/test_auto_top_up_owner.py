from types import SimpleNamespace

import pytest
from prepza_common.http import bearer

from app.constants.products import AUTO_TOP_UP_THRESHOLDS, NOT_YOUR_AUTO_TOP_UP
from app.service_auth import service_token
from app.services import auto_top_ups as service
from app.storage import auto_top_ups

AUTH = bearer(service_token("billing"))
URL = "/internal/companies/acme/auto-top-up"
CHOICE = {"product": "topup_1000", "threshold": AUTO_TOP_UP_THRESHOLDS[-1]}


@pytest.fixture
def running(monkeypatch):
    """Acme's automatic top-up runs on Ann's card; returns what was saved."""
    saved = []
    row = SimpleNamespace(
        subscription_id="sub_1",
        buyer_id="ann",
        product="topup_50",
        threshold=AUTO_TOP_UP_THRESHOLDS[0],
        failed_at=None,
        currency="USD",
    )

    async def get(owner_type, owner_id):
        return row

    async def save(owner_type, owner_id, product, threshold, buyer_id):
        saved.append((product, threshold, buyer_id))

        return row

    monkeypatch.setattr(service, "offered", lambda: True)
    monkeypatch.setattr(service, "products", lambda: ["topup_50", "topup_1000"])
    monkeypatch.setattr(auto_top_ups, "get", get)
    monkeypatch.setattr(auto_top_ups, "save", save)

    return saved


def test_another_member_cant_change_a_top_up_charged_to_someone_elses_card(client, running):
    response = client.put(URL, json=CHOICE, params={"buyer_id": "bob"}, headers=AUTH)

    assert response.status_code == 403
    assert response.json() == {"detail": NOT_YOUR_AUTO_TOP_UP}
    assert running == []


def test_the_cards_owner_changes_it(client, running):
    response = client.put(URL, json=CHOICE, params={"buyer_id": "ann"}, headers=AUTH)

    assert response.status_code == 200
    assert running == [("topup_1000", AUTO_TOP_UP_THRESHOLDS[-1], "ann")]
