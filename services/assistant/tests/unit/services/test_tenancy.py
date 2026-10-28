import asyncio

import httpx
import pytest
from fastapi import HTTPException

from assistant.integrations import companies
from assistant.services import tenancy


@pytest.fixture
def listed(monkeypatch):
    """Companies' list for the user: 150 companies, counting the reads."""
    state = {"reads": 0, "down": False}

    async def company_ids(user_id):
        state["reads"] += 1

        if state["down"]:
            raise httpx.ConnectError("companies is down")

        return [f"c{index}" for index in range(150)]

    monkeypatch.setattr(companies, "company_ids", company_ids)

    return state


def test_every_company_counts_past_a_hundred_and_one_confirm_reads_them_once(listed):
    first = asyncio.run(tenancy.user_companies("ann"))
    again = asyncio.run(tenancy.user_companies("ann"))
    fresh = asyncio.run(tenancy.user_companies("ann", fresh=True))

    assert len(first) == 150 and "c149" in first
    assert again == first == fresh
    # The second read was kept; a fresh one (after making a company) asks again.
    assert listed["reads"] == 2


def test_companies_not_answering_is_a_503(listed):
    listed["down"] = True

    with pytest.raises(HTTPException) as refused:
        asyncio.run(tenancy.user_companies("bob"))

    assert refused.value.status_code == 503
