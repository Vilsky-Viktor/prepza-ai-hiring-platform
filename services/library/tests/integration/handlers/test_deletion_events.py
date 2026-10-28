"""companies' interview.deleted and company.deleted take the questions of what went, through
library's events route (rule 11: a redelivery deletes nothing more, in any order)."""

import uuid

import httpx
from event_pushes import push

from library.main import app
from library.repositories import preparations
from tests.integration.factories import a_company, interview
from tests.integration.transactions import transaction


async def pushed(event_type: str, data: dict) -> list[int]:
    """The event pushed twice, as a redelivery would; the answers' codes."""
    event = push(event_type, data, str(uuid.uuid4()))
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://library") as client:
        return [(await client.post("/internal/events", json=event)).status_code for _ in "ab"]


async def kept(*set_ids) -> list[bool]:
    return [await transaction(preparations.get, set_id) is not None for set_id in set_ids]


def deleted(company: str, set_id=None, generation_id=None) -> dict:
    return {
        "interview_id": str(uuid.uuid4()),
        "company_id": company,
        "set_id": str(set_id) if set_id else None,
        "generation_id": str(generation_id) if generation_id else None,
    }


async def generation_of(set_id):
    question_set = await transaction(preparations.get, set_id)

    return question_set.generation_id


def test_a_deleted_interviews_set_goes_once_and_others_stay(run):
    company, other = a_company(str(uuid.uuid4())), a_company(str(uuid.uuid4()))

    async def scenario():
        gone = await interview("Gone", owner=company)
        same_company = await interview("Kept", owner=company)
        # Another company's event can't name this company's set.
        foreign = await interview("Foreign", owner=other)
        codes = await pushed("interview.deleted", deleted(company, gone))
        codes += await pushed("interview.deleted", deleted(company, foreign))

        return codes, await kept(gone, same_company, foreign)

    codes, left = run(scenario())

    assert codes == [204] * 4
    assert left == [False, True, True]


def test_a_set_saved_after_companies_looked_goes_by_its_generation(run):
    """Deleted while generating: the event names no set, but the generation that saved one."""
    company = a_company(str(uuid.uuid4()))

    async def scenario():
        late = await interview("Late", owner=company)
        await pushed("interview.deleted", deleted(company, None, await generation_of(late)))

        return await kept(late)

    assert run(scenario()) == [False]


def test_a_deleted_companys_sets_go_whatever_came_first(run, monkeypatch):
    """company.deleted before its interview's event, a batch at a time; templates and other
    companies' sets stay."""
    monkeypatch.setattr(preparations, "SET_DELETE_BATCH", 1)
    company, other = a_company(str(uuid.uuid4())), a_company(str(uuid.uuid4()))

    async def scenario():
        first = await interview("One", owner=company)
        second = await interview("Two", owner=company)
        others = await interview("Other", owner=other)
        template = await interview("Template", template=True)
        codes = await pushed("company.deleted", {"company_id": company})
        codes += await pushed("interview.deleted", deleted(company, first))

        return codes, await kept(first, second, others, template)

    codes, left = run(scenario())

    assert codes == [204] * 4
    assert left == [False, False, True, True]


def test_a_malformed_deletion_is_acknowledged_and_deletes_nothing(run):
    company = a_company(str(uuid.uuid4()))

    async def scenario():
        set_id = await interview("Stays", owner=company)
        codes = await pushed("company.deleted", {"company_id": "not-a-uuid"})
        codes += await pushed("interview.deleted", {"set_id": str(set_id)})

        return codes, await kept(set_id)

    assert run(scenario()) == ([204] * 4, [True])
