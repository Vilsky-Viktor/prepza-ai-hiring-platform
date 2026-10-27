"""The limits superadmins edit in Controls, and the AI costs tab's routes."""

import pytest
from prepza_common.limits.limit_list import LIMITS, PROVIDER_LIMITS

from app.routers import superadmin_ai as routes
from app.services import ai_costs, limit_hit_lists, limit_values
from app.storage import limit_hits, limit_settings

ANN = "ann@example.com"


@pytest.fixture
def kept(monkeypatch):
    """The changed limits and their history, in memory; syncing to Redis is counted."""
    state = {"values": {}, "changes": [], "syncs": 0}

    async def values():
        return dict(state["values"])

    async def change(name, value, user_id, email):
        old = state["values"].get(name)

        if value is None:
            state["values"].pop(name, None)
        else:
            state["values"][name] = value

        if old != value:
            state["changes"].append((name, old, value, email))

    async def sync():
        state["syncs"] += 1

    async def counts_since(start):
        return {"MAX_API_KEYS": 4, "OPENAI_QUOTA": 1}

    monkeypatch.setattr(limit_settings, "values", values)
    monkeypatch.setattr(limit_settings, "change", change)
    monkeypatch.setattr(limit_values, "sync", sync)
    monkeypatch.setattr(limit_hits, "counts_since", counts_since)

    return state


def shown(body, name):
    """A limit as the list shows it, an unpaid one inside its paid counterpart."""
    for found in body["limits"]:
        if found["name"] == name:
            return found

        if found["unpaid"] and found["unpaid"]["name"] == name:
            return found["unpaid"]


def test_a_superadmin_changes_a_limit_and_resets_it(client, signed_in, kept):
    signed_in(ANN)

    body = client.put("/superadmin/limits/MAX_API_KEYS", json={"value": 12}).json()

    assert (shown(body, "MAX_API_KEYS")["value"], shown(body, "MAX_API_KEYS")["changed"]) == (
        12,
        True,
    )

    body = client.delete("/superadmin/limits/MAX_API_KEYS").json()

    assert shown(body, "MAX_API_KEYS")["value"] == LIMITS["MAX_API_KEYS"].default
    assert not shown(body, "MAX_API_KEYS")["changed"]
    assert kept["changes"] == [("MAX_API_KEYS", None, 12, ANN), ("MAX_API_KEYS", 12, None, ANN)]
    # The services read Redis: written after each change.
    assert kept["syncs"] == 2


def test_setting_a_limit_to_its_default_is_a_reset(client, signed_in, kept):
    signed_in(ANN)
    kept["values"]["MAX_API_KEYS"] = 12
    client.put("/superadmin/limits/MAX_API_KEYS", json={"value": LIMITS["MAX_API_KEYS"].default})

    assert kept["values"] == {}


def test_a_counted_limit_is_whole_and_usd_keeps_its_cents(client, signed_in, kept):
    signed_in(ANN)
    client.put("/superadmin/limits/MAX_API_KEYS", json={"value": 11.6})
    client.put("/superadmin/limits/AI_SPEND_UNPAID_DAY", json={"value": 20.555})

    assert kept["values"] == {"MAX_API_KEYS": 12, "AI_SPEND_UNPAID_DAY": 20.55}


@pytest.mark.parametrize("value", [101, 0.4])
def test_a_value_out_of_its_bounds_is_refused(client, signed_in, kept, value):
    signed_in(ANN)

    response = client.put("/superadmin/limits/MAX_API_KEYS", json={"value": value})

    assert response.status_code == 422
    assert response.json() == {"detail": "Use a value from 1 to 100."}
    assert kept["changes"] == []


@pytest.mark.parametrize("value", [0, -5])
def test_zero_or_less_is_never_a_limit(client, signed_in, kept, value):
    signed_in(ANN)

    assert client.put("/superadmin/limits/MAX_API_KEYS", json={"value": value}).status_code == 422
    assert kept["changes"] == []


def test_a_plain_value_is_listed_without_hits_and_may_be_zero_where_its_bounds_allow(
    client, signed_in, kept
):
    signed_in(ANN)

    body = client.put("/superadmin/limits/MULTI_ANSWER_PERCENT", json={"value": 0}).json()
    share = shown(body, "MULTI_ANSWER_PERCENT")

    assert (share["value"], share["unit"], share["counted"], share["window"]) == (
        0,
        "percent",
        False,
        None,
    )
    assert shown(body, "MAX_API_KEYS")["counted"]
    assert kept["values"] == {"MULTI_ANSWER_PERCENT": 0}

    response = client.put("/superadmin/limits/QUESTION_SECONDS_HARD", json={"value": 5})

    assert response.status_code == 422
    assert response.json() == {"detail": "Use a value from 10 to 600."}


def test_an_unknown_limit_is_not_found(client, signed_in, kept):
    signed_in(ANN)

    response = client.put("/superadmin/limits/NO_SUCH", json={"value": 5})

    assert response.status_code == 404
    assert response.json() == {"detail": "No such limit."}


def test_the_list_pairs_unpaid_limits_with_paid_ones_and_counts_hits(client, signed_in, kept):
    signed_in(ANN)
    kept["values"]["INTERVIEWS_PER_DAY_UNPAID"] = 5

    body = client.get("/superadmin/limits").json()
    names = [found["name"] for found in body["limits"]]
    paid = shown(body, "INTERVIEWS_PER_DAY")

    assert "INTERVIEWS_PER_DAY_UNPAID" not in names
    assert (paid["unpaid"]["name"], paid["unpaid"]["value"]) == ("INTERVIEWS_PER_DAY_UNPAID", 5)
    assert shown(body, "MAX_API_KEYS")["hits"] == 4
    assert {found["name"]: found["hits"] for found in body["providers"]} == {
        name: 1 if name == "OPENAI_QUOTA" else 0 for name in PROVIDER_LIMITS
    }


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/superadmin/limits"),
        ("get", "/superadmin/limits/changes"),
        ("put", "/superadmin/limits/MAX_API_KEYS"),
        ("delete", "/superadmin/limits/MAX_API_KEYS"),
        ("get", "/superadmin/ai-costs"),
        ("get", "/superadmin/limit-hits"),
        ("get", "/superadmin/ai-spend?company_id=c1"),
    ],
)
def test_limits_and_ai_costs_are_not_found_for_others(client, signed_in, kept, method, path):
    signed_in("eve@example.com")

    response = getattr(client, method)(path, **({"json": {"value": 5}} if method == "put" else {}))

    assert response.status_code == 404
    assert kept["changes"] == []


def test_the_ai_costs_tab_asks_for_its_period(client, signed_in, monkeypatch):
    asked = []

    async def costs(period):
        asked.append(("costs", period))

        return {
            "totals": {
                "spend": 0,
                "calls": 0,
                "input_tokens": 0,
                "cached_input_tokens": 0,
                "output_tokens": 0,
            },
            "month": {"spend": 0, "budget": 0, "share": 0},
            "unpaid_today": {"spend": 0, "cap": 15, "share": 0},
            "categories": [],
            "actions": [],
            "models": [],
            "companies": [],
            "users": [],
            "by_month": False,
            "days": [],
        }

    async def hits(period):
        asked.append(("hits", period))

        return {"ours": [], "providers": []}

    monkeypatch.setattr(routes, "ai_costs_out", costs)
    monkeypatch.setattr(routes, "limit_hits_out", hits)
    signed_in(ANN)

    assert client.get("/superadmin/ai-costs?period=2026-10").status_code == 200
    assert client.get("/superadmin/limit-hits?period=2026").status_code == 200
    assert client.get("/superadmin/ai-costs?period=october").status_code == 422
    assert asked == [("costs", "2026-10"), ("hits", "2026")]


def test_a_support_pages_ai_spend_names_a_company_or_a_user(client, signed_in, monkeypatch):
    async def spend_of(column, value, start, end):
        return 1.5, 3

    monkeypatch.setattr(ai_costs.ai_costs, "spend_of", spend_of)
    signed_in(ANN)

    response = client.get("/superadmin/ai-spend")

    assert response.status_code == 422
    assert response.json() == {"detail": "Name a company or a user"}
    assert client.get("/superadmin/ai-spend?user_id=u1").json() == {
        "spend": 1.5,
        "calls": 3,
        "days": 30,
    }


def test_limit_hitters_keep_only_the_top_few_per_limit():
    rows = [("A", f"c{i}", 10 - i) for i in range(8)] + [("B", "c1", 2)]

    found = limit_hit_lists.top_by_limit(rows)

    assert [key for key, _ in found["A"]] == ["c0", "c1", "c2", "c3", "c4"]
    assert found["B"] == [("c1", 2)]
