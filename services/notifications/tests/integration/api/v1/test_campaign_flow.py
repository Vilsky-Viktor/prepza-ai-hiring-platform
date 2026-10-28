import json
import os
import uuid
from datetime import UTC, datetime

import httpx
import pytest
from prepza_common.auth.auth import current_user
from prepza_common.auth.user import User
from prepza_common.db.lock_waits import hold_first_commit, race

from notifications.config import settings
from notifications.constants.campaigns import ALREADY_SENT, ONE_A_DAY
from notifications.helpers.unsubscribe import address_hash
from notifications.main import app
from notifications.repositories import bulk_sends, suppressed
from notifications.repositories import campaigns as campaigns_store
from notifications.schemas.campaigns import CampaignIn, CampaignTexts
from notifications.services import bulk, campaign_sends, campaigns
from notifications.services import outbox as outbox_service
from tests.integration.factories import api, marked_sent, receive
from tests.integration.transactions import transaction

MAILPIT = os.getenv("MAILPIT_URL", "http://mailpit:8025")
SECRET = "whsec_dGVzdC13ZWJob29rLWtleQ=="
ENGLISH = {"subject": "Code questions", "text": "Now with code.", "button": None}


def fields(kind: str, link: str | None = None) -> dict:
    """A campaign's columns besides its texts: to everyone."""
    return {"kind": kind, "groups": [], "editors_only": False, "company_ids": [], "link": link}


async def large_resend_quota(redis):
    """Resend's daily quota edited far above what the tests send, so emails other tests sent
    today never use up the bulk share."""
    return {"RESEND_DAILY_LIMIT": 1_000_000}


@pytest.fixture
def quiet(monkeypatch):
    """Generation isn't asked to translate; sending isn't paced."""

    async def translate(campaign_id):
        return None

    async def no_wait(_seconds):
        return None

    monkeypatch.setattr(campaigns.generation, "translate_campaign", translate)
    monkeypatch.setattr("notifications.services.bulk.asyncio.sleep", no_wait)


def test_a_campaign_goes_from_start_to_mailpit_once_and_only_to_who_chose_it(
    run, quiet, monkeypatch
):
    user = f"c{uuid.uuid4().hex[:12]}"
    address = f"{user}@example.com"

    async def user_ids(after, setting=None):
        return [user, "guest-x"] if setting == "promotions" else []

    async def recipients(ids):
        return [
            {
                "user_id": user,
                "email": address,
                "language": "en",
                "preferences": {"promotions": True},
            }
            for one in ids
            if one == user
        ]

    monkeypatch.setattr("notifications.services.audiences.library.user_ids", user_ids)
    monkeypatch.setattr(bulk.library, "recipients", recipients)
    monkeypatch.setattr(settings, "resend_api_key", "")
    monkeypatch.setattr("prepza_common.limits.limits.current_values", large_resend_quota)

    async def scenario():
        campaign = await transaction(campaigns_store.create, fields("promotions"), "sam", ENGLISH)
        send_id = await marked_sent(campaign.id, "promotions", "sam", 1)
        again = await marked_sent(campaign.id, "promotions", "sam", 1)
        await bulk.prepare(
            await transaction(bulk_sends.get, "promotions", str(campaign.id)), until=0
        )
        await bulk.send_bulk(datetime.now(UTC))
        counts = (await transaction(bulk_sends.counts, [send_id]))[send_id]

        async with httpx.AsyncClient(base_url=MAILPIT) as mailpit:
            found = (await mailpit.get("/api/v1/search", params={"query": f"to:{address}"})).json()
            ids = [message["ID"] for message in found["messages"]]
            await mailpit.request("DELETE", "/api/v1/messages", json={"IDs": ids})

        return again, counts, found

    again, counts, found = run(scenario())

    assert again == ALREADY_SENT
    assert (counts["sent"], counts["pending"]) == (1, 0)
    assert [message["Subject"] for message in found["messages"]] == [ENGLISH["subject"]]


def test_a_kinds_campaigns_a_day_stay_within_the_limit_even_sent_at_once(run, quiet, monkeypatch):
    """At a limit of 2 a day (CAMPAIGNS_PER_KIND_DAY as edited), one sent, then two at once: the
    second waits on the kind's lock until the first commits, and only the first goes. No other
    test sends an "updates" campaign, in a database of their own."""

    async def scenario():
        drafts = [
            await transaction(campaigns_store.create, fields("updates"), "sam", ENGLISH)
            for _ in range(3)
        ]
        await marked_sent(drafts[0].id, "updates", "sam", 2)
        held = hold_first_commit(monkeypatch, campaign_sends)

        return await race(
            os.environ["DATABASE_URL"],
            held,
            *(marked_sent(draft.id, "updates", "sam", 2) for draft in drafts[1:]),
        )

    first, second = run(scenario())

    assert isinstance(first, uuid.UUID)
    assert second == ONE_A_DAY


def test_a_changed_english_drops_the_translations_but_a_hand_edit_survives_a_late_job(run, quiet):
    async def scenario():
        campaign = await transaction(
            campaigns_store.create, fields("updates", "/pricing"), "sam", ENGLISH
        )
        await campaigns.set_texts(
            campaign.id, "de", CampaignTexts(**{**ENGLISH, "subject": "Von Hand"})
        )
        await campaigns.save_translations(
            campaign.id,
            ENGLISH,
            {
                "de": {**ENGLISH, "subject": "Maschine"},
                "fr": {**ENGLISH, "subject": "Machine"},
            },
        )
        _, kept = await transaction(campaigns_store.get, campaign.id)
        changed = {**ENGLISH, "text": "Now with more code.", "button": "See the prices"}
        await campaigns.update(campaign.id, CampaignIn(kind="updates", link="/pricing", **changed))
        # A job that translated the old text arrives late: dropped.
        await campaigns.save_translations(campaign.id, ENGLISH, {"de": ENGLISH})
        _, after = await transaction(campaigns_store.get, campaign.id)

        return kept, after

    kept, after = run(scenario())

    assert (kept["de"]["subject"], kept["fr"]["subject"]) == ("Von Hand", "Machine")
    assert list(after) == ["en"]


def test_a_signed_complaint_puts_the_address_on_the_suppression_list(run, monkeypatch):
    address = f"s{uuid.uuid4().hex[:12]}@example.com"
    monkeypatch.setattr(settings, "resend_webhook_secret", SECRET)

    async def unsubscribe(user_id, email_settings):
        return None

    monkeypatch.setattr("notifications.services.unsubscribe.library.unsubscribe", unsubscribe)
    event = {"type": "email.complained", "data": {"to": [address], "tags": {"kind": "updates"}}}
    body = json.dumps(event).encode()

    async def unpublished():
        return None

    # The test pushes the recorded event back itself, as Pub/Sub would (receive).
    monkeypatch.setattr(outbox_service, "flush_quietly", unpublished)

    async def scenario():
        async with api() as client:
            answers = await receive(client, SECRET, body)

        found = await transaction(suppressed.among, [address_hash(address)])
        await transaction(suppressed.remove, address_hash(address))

        return answers, found

    answers, found = run(scenario())

    assert answers == (204, 204)
    assert found == {address_hash(address)}


def test_a_news_post_becomes_a_product_update_with_a_button_to_it(run, quiet, monkeypatch):
    news_id, gone_id = uuid.uuid4(), uuid.uuid4()
    monkeypatch.setenv("SUPERADMIN_EMAILS", "sam@prepza.dev")
    app.dependency_overrides[current_user] = lambda: User(
        uid="sam",
        email="sam@prepza.dev",
        email_verified=True,
        sign_in_provider="google.com",
    )

    async def news_post(post_id):
        return (
            {"title": "Code questions", "text": "Now **with** code."}
            if post_id == str(news_id)
            else None
        )

    monkeypatch.setattr(campaigns.library, "news_post", news_post)

    async def scenario():
        async with api() as client:
            made = await client.post(f"/superadmin/campaigns/from-news/{news_id}")
            gone = await client.post(f"/superadmin/campaigns/from-news/{gone_id}")

        return made, gone

    try:
        made, gone = run(scenario())
    finally:
        app.dependency_overrides.clear()

    campaign = made.json()
    assert made.status_code == 201
    assert (campaign["kind"], campaign["status"], campaign["link"]) == (
        "updates",
        "draft",
        f"/news#{news_id}",
    )
    assert campaign["texts"]["en"]["subject"] == "Code questions"
    assert campaign["texts"]["en"]["text"] == "Now **with** code."
    assert campaign["texts"]["en"]["button"]
    assert gone.status_code == 404
