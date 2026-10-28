import asyncio
import uuid

import httpx
import pytest
from fastapi import HTTPException
from prepza_common.http import http
from prepza_common.limits import limits

from ats.constants.ats import TEAMTAILOR_HOSTS
from ats.integrations import teamtailor
from ats.integrations.ats_http import calling_company
from ats.models.ats import AtsConnection
from ats.services import ats as integrations

COMPANY_ID = uuid.uuid4()
HOST = TEAMTAILOR_HOSTS[0]


@pytest.fixture
def busy(monkeypatch):
    """Teamtailor answering with `status`; returns the limit hits recorded."""
    state = {"status": 429, "hits": []}

    def handler(request):
        return httpx.Response(state["status"], json={})

    async def publish(event_type, data, attempts, timeout):
        state["hits"].append(data)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    monkeypatch.setattr(http, "get_client", lambda: client)
    monkeypatch.setattr(limits, "publish_retried", publish)

    return state


async def application_for(company_id):
    """Reads an application as `company_id`'s connection does (its credentials set the company)."""
    calling_company.set(company_id)

    return await teamtailor.application(HOST, "key", "55")


def test_an_ats_429_is_recorded_as_its_rate_limits_hit_for_the_calling_company(busy):
    with pytest.raises(HTTPException) as refused:
        asyncio.run(application_for(COMPANY_ID))

    assert refused.value.status_code == 429
    assert busy["hits"] == [
        {
            "limit": "ATS_RATE_LIMIT",
            "kind": "provider:teamtailor",
            "scope": "company",
            "company_id": str(COMPANY_ID),
            "user_id": None,
            "what": None,
        }
    ]


def test_an_ats_answer_that_isnt_429_records_nothing(busy):
    busy["status"] = 200

    asyncio.run(application_for(COMPANY_ID))

    assert busy["hits"] == []


def test_reading_a_connections_key_makes_its_ats_calls_its_companys(busy, key):
    connection = AtsConnection(
        company_id=COMPANY_ID,
        provider="teamtailor",
        credentials=integrations.seal({"host": HOST, "key": "k"}),
    )

    async def scenario():
        found = await integrations.credentials(connection)

        return await teamtailor.application(found["host"], found["key"], "55")

    with pytest.raises(HTTPException):
        asyncio.run(scenario())

    assert [(hit["kind"], hit["company_id"]) for hit in busy["hits"]] == [
        ("provider:teamtailor", str(COMPANY_ID))
    ]
