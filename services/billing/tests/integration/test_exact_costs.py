"""AI costs are kept and summed exactly: ten calls of a tenth of a dollar make a dollar, where
floats would make 0.9999999999999999."""

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.models.usage import AiUsage
from app.storage import ai_costs, usage
from tests.integration.test_ai_usage import call, rows_of

NOW = datetime(2026, 10, 10, 12, tzinfo=UTC)


def test_ten_tenths_of_a_dollar_make_a_dollar(run):
    company = str(uuid.uuid4())

    async def scenario():
        for _ in range(10):
            await usage.store_usage(uuid.uuid4().hex, NOW, call(company_id=company, cost_usd=0.1))

        spend, calls = await ai_costs.spend_of(
            AiUsage.company_id, company, NOW - timedelta(hours=1), NOW + timedelta(hours=1)
        )

        return spend, calls, {row.cost for row in await rows_of(AiUsage.company_id, company)}

    spend, calls, kept = run(scenario())

    assert (spend, calls) == (1.0, 10)
    assert kept == {Decimal("0.1")}
