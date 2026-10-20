import asyncio
import json
import os
import uuid
from datetime import UTC, datetime

import httpx
import pytest
from prepza_common.auth import current_user
from prepza_common.user import User

from app.config.settings import settings
from app.constants.campaigns import ALREADY_SENT, ONE_A_DAY
from app.helpers.unsubscribe import address_hash
from app.main import app
from app.services import bulk, campaigns
from app.storage import bulk_sends, suppressed
from app.storage import campaigns as campaigns_store
from tests.integration.factories import api, signed

MAILPIT = os.getenv("MAILPIT_URL", "http://mailpit:8025")
SECRET = "whsec_dGVzdC13ZWJob29rLWtleQ=="
ENGLISH = {"subject": "Code questions", "text": "Now with code.", "button": None}


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
    monkeypatch.setattr("app.services.bulk.asyncio.sleep", no_wait)


def test_a_campaign_goes_from_start_to_mailpit_once_and_only_to_who_chose_it(
    run, quiet, monkeypatch
):
    user = f"c{uuid.uuid4().hex[:12]}"
    address = f"{user}@example.com"

    async def user_ids(setting=None):
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

    monkeypatch.setattr("app.services.bulk_content.library.user_ids", user_ids)
    monkeypatch.setattr(bulk.library, "recipients", recipients)
    monkeypatch.setattr(settings, "resend_api_key", "")
    monkeypatch.setattr("prepza_common.limits.current_values", large_resend_quota)

    async def scenario():
        campaign = await campaigns_store.create("promotions", None, "sam", ENGLISH)
        send_id = await campaigns_store.mark_sent(campaign.id, "sam", 1)
        again = await campaigns_store.mark_sent(campaign.id, "sam", 1)
        await bulk.prepare(await bulk_sends.get("promotions", str(campaign.id)))
        await bulk.send_bulk(datetime.now(UTC))
        counts = (await bulk_sends.counts([send_id]))[send_id]

        async with httpx.AsyncClient(base_url=MAILPIT) as mailpit:
            found = (await mailpit.get("/api/v1/search", params={"query": f"to:{address}"})).json()
            ids = [message["ID"] for message in found["messages"]]
            await mailpit.request("DELETE", "/api/v1/messages", json={"IDs": ids})

        return again, counts, found

    again, counts, found = run(scenario())

    assert again == ALREADY_SENT
    assert (counts["sent"], counts["pending"]) == (1, 0)
    assert [message["Subject"] for message in found["messages"]] == [ENGLISH["subject"]]


def test_a_kinds_campaigns_a_day_stay_within_the_limit_even_sent_at_once(run, quiet):
    """At a limit of 2 a day (CAMPAIGNS_PER_KIND_DAY as edited), three sent at once: two go.
    No other test sends an "updates" campaign, in a database of their own."""

    async def scenario():
        drafts = [await campaigns_store.create("updates", None, "sam", ENGLISH) for _ in range(3)]

        return await asyncio.gather(
            *(campaigns_store.mark_sent(draft.id, "sam", 2) for draft in drafts)
        )

    outcomes = run(scenario())

    assert sorted(map(str, outcomes)).count(ONE_A_DAY) == 1
    assert len([one for one in outcomes if isinstance(one, uuid.UUID)]) == 2


def test_a_changed_english_drops_the_translations_but_a_hand_edit_survives_a_late_job(run):
    async def scenario():
        campaign = await campaigns_store.create("updates", "/pricing", "sam", ENGLISH)
        await campaigns_store.set_texts(campaign.id, "de", {**ENGLISH, "subject": "Von Hand"})
        await campaigns_store.save_translations(
            campaign.id,
            ENGLISH,
            {
                "de": {**ENGLISH, "subject": "Maschine"},
                "fr": {**ENGLISH, "subject": "Machine"},
            },
        )
        _, kept = await campaigns_store.get(campaign.id)
        changed = {**ENGLISH, "text": "Now with more code."}
        await campaigns_store.update(campaign.id, "updates", "/pricing", changed)
        # A job that translated the old text arrives late: dropped.
        await campaigns_store.save_translations(campaign.id, ENGLISH, {"de": ENGLISH})
        _, after = await campaigns_store.get(campaign.id)

        return kept, after

    kept, after = run(scenario())

    assert (kept["de"]["subject"], kept["fr"]["subject"]) == ("Von Hand", "Machine")
    assert list(after) == ["en"]


def test_a_signed_complaint_puts_the_address_on_the_suppression_list(run, monkeypatch):
    address = f"s{uuid.uuid4().hex[:12]}@example.com"
    monkeypatch.setattr(settings, "resend_webhook_secret", SECRET)

    async def unsubscribe(user_id, email_settings):
        return None

    monkeypatch.setattr("app.services.unsubscribe.library.unsubscribe", unsubscribe)
    event = {"type": "email.complained", "data": {"to": [address], "tags": {"kind": "updates"}}}
    body = json.dumps(event).encode()

    async def scenario():
        async with api() as client:
            response = await client.post(
                "/webhooks/resend", content=body, headers=signed(body, SECRET)
            )

        found = await suppressed.among([address_hash(address)])
        await suppressed.remove(address_hash(address))

        return response, found

    response, found = run(scenario())

    assert response.status_code == 204
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
