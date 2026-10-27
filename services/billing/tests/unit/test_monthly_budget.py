"""The AI costs tab's month: its spend against the monthly budget set in Controls."""

import asyncio

import pytest
from fake_redis import FakeRedis
from prepza_common.redis import memory_cache

from app.services import ai_costs
from app.storage import ai_costs as ai_costs_storage


@pytest.mark.parametrize(
    ("edited", "budget", "share"),
    [({}, 300.0, 0.25), ({"MONTHLY_BUDGET": "150"}, 150.0, 0.5), ({"MONTHLY_BUDGET": "0"}, 0, 0)],
)
def test_the_months_spend_is_a_share_of_the_budget_set_in_controls(
    monkeypatch, edited, budget, share
):
    async def totals(where):
        return 75.0, 10, 0, 0, 0

    monkeypatch.setattr(memory_cache, "_entries", {})
    monkeypatch.setattr(ai_costs_storage, "totals", totals)
    monkeypatch.setattr(ai_costs, "get_redis", lambda: FakeRedis(edited))

    month = asyncio.run(ai_costs.month_out())

    assert (month.spend, month.budget, month.share) == (75.0, budget, share)
