"""The AI costs tab's monthly budget as set in Controls, against the real database and Redis."""

import pytest
from prepza_common.auth.user import User
from prepza_common.limits.limit_list import LIMITS_KEY
from prepza_common.redis import memory_cache

from billing.services import ai_costs, limit_values

ANN = User(uid="ann", email="ann@example.com", email_verified=True)


@pytest.fixture
def reset(run, redis):
    """The budget back at its default after the test."""
    yield

    run(limit_values.change("MONTHLY_BUDGET", None, ANN))


def test_a_budget_edited_in_controls_is_what_the_month_is_compared_with(run, redis, reset):
    async def month_at(value):
        await limit_values.change("MONTHLY_BUDGET", value, ANN)
        # Past the 30 seconds' cache, as the tab reads it then.
        memory_cache._entries.pop(LIMITS_KEY, None)

        return await ai_costs.month_out()

    async def scenario():
        return await month_at(200), await month_at(0)

    edited, none = run(scenario())

    assert edited.budget == 200
    assert edited.share == pytest.approx(edited.spend / 200)
    # 0: no budget, so no share.
    assert (none.budget, none.share) == (0, 0)
