import os
import uuid
from datetime import UTC, datetime

import httpx
import pytest
from sqlalchemy.exc import IntegrityError

from notifications.config import settings
from notifications.constants.campaigns import CHANGED
from notifications.helpers.unsubscribe import address_hash
from notifications.repositories import bulk_sends, suppressed
from notifications.repositories import campaigns as campaigns_store
from notifications.services import bulk, campaigns
from tests.integration.factories import marked_sent
from tests.integration.transactions import transaction

MAILPIT = os.getenv("MAILPIT_URL", "http://mailpit:8025")
ENGLISH = {"subject": "Planned downtime", "text": "Down on Sunday.", "button": None}


def fields(kind: str, groups=(), editors_only=False, company_ids=()) -> dict:
    return {
        "kind": kind,
        "groups": list(groups),
        "editors_only": editors_only,
        "company_ids": list(company_ids),
        "link": None,
    }


async def large_resend_quota(redis):
    """Resend's daily quota edited far above what the tests send, so emails other tests sent
    today never use up the bulk share."""
    return {"RESEND_DAILY_LIMIT": 1_000_000}


@pytest.fixture
def people(monkeypatch):
    """Three accounts of this test's own: a company owner who is also a candidate, a learner
    with every optional email off, and a candidate whose address is suppressed; the address
    taken off the list again afterwards."""
    ann, lea, sup = (f"n{uuid.uuid4().hex[:12]}" for _ in range(3))

    async def translate(campaign_id, source):
        return None

    async def no_wait(_seconds):
        return None

    async def member_ids(after, editors_only):
        return [user for user in [ann] if user > after]

    async def rounds_ids(group, after):
        users = {"candidates": sorted([ann, sup]), "learners": [lea]}[group]

        return [user for user in users if user > after]

    async def recipients(ids):
        return [
            {"user_id": one, "email": f"{one}@example.com", "language": "en", "preferences": {}}
            for one in ids
        ]

    monkeypatch.setattr(campaigns.generation, "translate_campaign", translate)
    monkeypatch.setattr("notifications.services.bulk.asyncio.sleep", no_wait)
    monkeypatch.setattr("notifications.services.audiences.companies.member_ids", member_ids)
    monkeypatch.setattr("notifications.services.audiences.rounds.user_ids", rounds_ids)
    monkeypatch.setattr(bulk.accounts, "recipients", recipients)
    monkeypatch.setattr(settings, "resend_api_key", "")
    monkeypatch.setattr("testee_common.limits.limits.current_values", large_resend_quota)

    yield ann, lea, sup


def test_a_notice_reaches_its_groups_once_each_whatever_their_settings(run, people):
    ann, lea, sup = people

    async def scenario():
        await transaction(suppressed.add, address_hash(f"{sup}@example.com"), "bounced")
        groups = ["members", "candidates", "learners"]
        campaign = await transaction(
            campaigns_store.create, fields("notices", groups), "sam", ENGLISH
        )
        send_id = await marked_sent(campaign.id, "notices", "sam", 1)
        await bulk.prepare(
            await transaction(bulk_sends.get, "notices", str(campaign.id)), until=1e12
        )
        await bulk.send_bulk(datetime.now(UTC))
        counts = (await transaction(bulk_sends.counts, [send_id]))[send_id]
        found = {}

        async with httpx.AsyncClient(base_url=MAILPIT) as mailpit:
            for user in (ann, lea, sup):
                search = {"query": f"to:{user}@example.com"}
                messages = (await mailpit.get("/api/v1/search", params=search)).json()["messages"]
                found[user] = [
                    (await mailpit.get(f"/api/v1/message/{one['ID']}/headers")).json()
                    for one in messages
                ]
                ids = [one["ID"] for one in messages]
                await mailpit.request("DELETE", "/api/v1/messages", json={"IDs": ids})

        await transaction(suppressed.remove, address_hash(f"{sup}@example.com"))

        return counts, found

    counts, found = run(scenario())

    # Ann, a member and a candidate, gets one; Lea, with every optional email off, gets it too.
    assert (len(found[ann]), len(found[lea]), len(found[sup])) == (1, 1, 0)
    assert (counts["sent"], counts["skipped"]) == (2, 1)
    headers = found[ann][0]
    assert "List-Unsubscribe" not in headers
    assert headers["From"] == [settings.mail_from]


def test_a_notice_keeps_its_own_day_limit_and_a_changed_kind_is_refused(run, people):
    async def scenario():
        notice = await transaction(campaigns_store.create, fields("notices"), "sam", ENGLISH)
        changed = await marked_sent(notice.id, "updates", "sam", 1)
        # An update sent today counts against the updates only.
        update = await transaction(campaigns_store.create, fields("updates"), "sam", ENGLISH)
        await marked_sent(update.id, "updates", "sam", 1_000)
        sent = await marked_sent(notice.id, "notices", "sam", 1_000)

        return changed, sent

    changed, sent = run(scenario())

    assert changed == CHANGED
    assert isinstance(sent, uuid.UUID)


@pytest.mark.parametrize(
    "chosen",
    [
        # Owners and admins only, without companies.
        fields("notices", ["learners"], editors_only=True),
        # Some companies only, for a product update.
        fields("updates", ["members"], company_ids=[uuid.uuid4()]),
        # A group that isn't one.
        fields("notices", ["everyone"]),
    ],
)
def test_the_database_refuses_an_audience_the_service_would(run, chosen):
    with pytest.raises(IntegrityError):
        run(transaction(campaigns_store.create, chosen, "sam", ENGLISH))
