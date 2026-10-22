import pytest

from app.integrations import billing, companies, generation, library
from app.integrations.resend import ResendBusy
from app.services import delivery, member_pages
from app.storage import digest_activity, sent_emails, suppressed
from tests.unit.member_world import COMPANY, finished, person


@pytest.fixture(autouse=True)
def nothing_suppressed(monkeypatch):
    """No address is on the suppression list unless a test puts it there: unit tests have no
    database (tests/integration checks the real list)."""

    async def get(address):
        return None

    monkeypatch.setattr(suppressed, "get", get)


@pytest.fixture(autouse=True)
def unpaced(monkeypatch):
    """Every request to Resend fits its second, counted nowhere: unit tests have no Redis
    (tests/integration paces against a real one)."""

    async def wait_turn(redis, key, per_second):
        return False

    monkeypatch.setattr(delivery, "wait_turn", wait_turn)


@pytest.fixture
def world(monkeypatch):
    """Other services, the sent log and delivery, faked; returns what was sent and claimed."""
    state = {
        "sent": [],
        "claims": [],
        "released": [],
        "people": [person("ann"), person("vic")],
        "low": [{"company_id": "c1", "available": 100}],
        "busy": False,
        "companies": [COMPANY],
        "activity": [finished("c1")],
        "asked_companies": [],
        "pages": [],
        "waiting_pages": [],
        "cursors": {},
    }

    async def members(company_ids):
        return [company for company in state["companies"] if company["id"] in company_ids]

    async def company_ids(user_id):
        state["asked_companies"].append(user_id)

        return [
            company["id"]
            for company in state["companies"]
            if any(member["user_id"] == user_id for member in company["members"])
        ]

    async def recipients(user_ids):
        return [found for found in state["people"] if found["user_id"] in user_ids]

    async def low_companies():
        return state["low"]

    async def waiting(ready, started, company_ids):
        state["waiting_of"] = company_ids
        idle = [{"id": "i1", "company_id": "c1", "title": "Backend"}]

        return {
            "without_candidates": [row for row in idle if row["company_id"] in company_ids],
            "being_generated": [],
        }

    async def waiting_company_ids(ready, started, after, limit):
        state["waiting_pages"].append(after)

        return [company_id for company_id in ["c1"] if company_id > after][:limit]

    async def statuses(ids):
        return []

    async def claim(user_id, kind, today, every_days, items=()):
        # Once a day for each user and kind, as the sent log has it.
        if (user_id, kind, today) in [claimed[:3] for claimed in state["claims"]]:
            return None

        state["claims"].append((user_id, kind, today, every_days, list(items)))

        return list(items)

    async def release(user_id, kind, today, items):
        state["released"].append((user_id, kind))

    async def send(email, key):
        if state["busy"]:
            raise ResendBusy()

        state["sent"].append((email, key))

    async def active_companies(kinds, since, until, after, limit):
        state["window"] = (since, until)
        state["pages"].append(after)

        active = sorted({item.recipient_id for item in state["activity"]})

        return [company_id for company_id in active if company_id > after][:limit]

    async def companies_activity(kinds, since, until, company_ids):
        return [item for item in state["activity"] if item.recipient_id in company_ids]

    async def cursor(job, day):
        return state["cursors"].get((job, day), "")

    async def move_cursor(job, day, after):
        state["cursors"][(job, day)] = after

    async def no_wait(seconds):
        return None

    monkeypatch.setattr(companies, "members", members)
    monkeypatch.setattr(companies, "waiting_interviews", waiting)
    monkeypatch.setattr(companies, "waiting_company_ids", waiting_company_ids)
    monkeypatch.setattr(library, "recipients", recipients)
    monkeypatch.setattr(billing, "low_companies", low_companies)
    monkeypatch.setattr(generation, "statuses", statuses)
    monkeypatch.setattr(sent_emails, "claim", claim)
    monkeypatch.setattr(sent_emails, "release", release)
    monkeypatch.setattr(delivery, "send", send)
    monkeypatch.setattr(companies, "company_ids", company_ids)
    monkeypatch.setattr(digest_activity, "active_companies", active_companies)
    monkeypatch.setattr(digest_activity, "companies_activity", companies_activity)
    monkeypatch.setattr(member_pages, "cursor", cursor)
    monkeypatch.setattr(member_pages, "move_cursor", move_cursor)
    monkeypatch.setattr("app.services.member_sends.asyncio.sleep", no_wait)

    return state
