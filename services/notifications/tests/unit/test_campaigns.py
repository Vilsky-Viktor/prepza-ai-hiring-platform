import asyncio
import re
import uuid
from html import unescape
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from prepza_common import memory_cache
from prepza_common.auth import current_user
from prepza_common.user import User

from app.constants.campaigns import ALREADY_SENT, LINK_NOT_ON_SITE, NO_BUTTON_TEXT, ONE_A_DAY
from app.helpers.campaign_emails import campaign_email
from app.helpers.unsubscribe import address_hash, verify
from app.main import app
from app.schemas.campaigns import CampaignIn
from app.services import campaign_sends, campaigns, unsubscribe
from app.storage import bulk_recipients, suppressed
from app.storage import campaigns as campaigns_store

SECRET = "test-email-link-secret"
SITE = "https://prepza.com"
TEXTS = {
    "en": {
        "subject": "Code questions",
        "text": "Now with **code**.\nTry it.\n\nA <b>second</b> one.",
        "button": "See it",
    },
    "de": {"subject": "Code-Fragen", "text": "Jetzt mit Code.", "button": "Ansehen"},
}


def person(user_id, language="en", **preferences):
    return {
        "user_id": user_id,
        "email": f"{user_id}@example.com",
        "language": language,
        "preferences": preferences,
    }


def test_the_email_is_in_the_users_language_with_its_settings_unsubscribe_and_the_send():
    email = campaign_email("updates", person("ann", "de"), TEXTS, "/news#1", SITE, SECRET, "s-1")

    assert email.subject == "Code-Fragen"
    assert email.optional and email.tags == {"kind": "updates", "id": "ann", "send": "s-1"}
    assert f"{SITE}/news#1" in email.text and "Ansehen" in email.text
    [token, *_] = re.findall(r"/unsubscribe\?token=([\w.-]+)", unescape(email.text))
    assert verify(token, SECRET) == {"type": "updates", "user_id": "ann"}
    assert "List-Unsubscribe" in email.headers


def test_a_language_without_texts_gets_the_english_its_markdown_formatted_and_html_escaped():
    email = campaign_email("promotions", person("ann", "fr"), TEXTS, None, SITE, SECRET)

    assert email.subject == "Code questions"
    assert re.search(r"<strong[^>]*>code</strong>\.<br>\s*Try it\.</p>", email.html)
    assert "&lt;b&gt;second&lt;/b&gt;" in email.html and "<b>" not in email.html
    # The preheader is the text's words, without its marks.
    assert "Now with code. Try it. A" in email.html
    # Without a link, the button opens the site; a test has no send.
    assert f"{SITE}/" in email.text and "send" not in email.tags
    assert verify(re.findall(r"token=([\w.-]+)", unescape(email.text))[0], SECRET)["type"] == (
        "promotions"
    )


@pytest.mark.parametrize(
    ("link", "button", "error"),
    [
        ("https://evil.example", "Go", LINK_NOT_ON_SITE),
        ("//evil.example", "Go", LINK_NOT_ON_SITE),
        ("/pricing", None, NO_BUTTON_TEXT),
    ],
)
def test_the_button_opens_a_page_on_the_site_and_has_a_text(link, button, error):
    body = CampaignIn(kind="updates", subject="S", text="T", button=button, link=link)

    with pytest.raises(HTTPException) as refused:
        campaigns.checked(body)

    assert refused.value.detail == error


def test_the_recipients_are_users_with_the_setting_on_with_an_address_not_suppressed(monkeypatch):
    asked = []

    async def get(campaign_id):
        return SimpleNamespace(kind="promotions"), TEXTS

    async def user_ids(setting=None):
        asked.append(setting)

        return ["ann", "bob", "cat", "guest-1"]

    async def recipients(ids):
        assert "guest-1" not in ids

        return [person("ann", promotions=True), person("bob", promotions=True), person("cat")]

    async def among(hashes):
        return {address_hash("bob@example.com")} & set(hashes)

    monkeypatch.setattr(campaigns_store, "get", get)
    monkeypatch.setattr("app.services.bulk_content.library.user_ids", user_ids)
    monkeypatch.setattr(campaign_sends.library, "recipients", recipients)
    monkeypatch.setattr(suppressed, "among", among)

    assert asyncio.run(campaign_sends.recipients_count(uuid.uuid4())) == 1
    assert asked == ["promotions"]


class EditedLimits:
    """Redis holding the limits as the Controls tab edited them."""

    def __init__(self, values: dict):
        self.values = values

    async def hgetall(self, key):
        return {name.encode(): str(value).encode() for name, value in self.values.items()}


@pytest.mark.parametrize(
    ("outcome", "edited", "code", "detail"),
    [
        (ALREADY_SENT, {}, 409, "This campaign was already sent, so it can't be changed."),
        (
            ONE_A_DAY,
            {},
            429,
            "Today's limit of campaigns of this kind (1) is reached. Send the next one tomorrow.",
        ),
        (
            ONE_A_DAY,
            {"CAMPAIGNS_PER_KIND_DAY": 3},
            429,
            "Today's limit of campaigns of this kind (3) is reached. Send the next one tomorrow.",
        ),
    ],
)
def test_a_second_send_or_one_over_the_kinds_limit_today_is_refused(
    monkeypatch, outcome, edited, code, detail
):
    """The day's limit of a kind is as edited in Controls, and a refusal over it is recorded."""
    asked, hits = [], []

    async def mark_sent(campaign_id, user_id, per_day):
        asked.append(per_day)

        return outcome

    async def record_hit(name, **who):
        hits.append((name, who))

    monkeypatch.setattr(memory_cache, "_entries", {})
    monkeypatch.setattr(campaign_sends, "get_redis", lambda: EditedLimits(edited))
    monkeypatch.setattr(campaign_sends, "record_hit", record_hit)
    monkeypatch.setattr(campaigns_store, "mark_sent", mark_sent)

    with pytest.raises(HTTPException) as refused:
        asyncio.run(campaign_sends.send(uuid.uuid4(), "sam"))

    assert (refused.value.status_code, refused.value.detail) == (code, detail)
    # The day's limit says when it frees up; a campaign sent already never does.
    assert ("Retry-After" in (refused.value.headers or {})) == (outcome == ONE_A_DAY)
    assert asked == [edited.get("CAMPAIGNS_PER_KIND_DAY", 1)]
    assert hits == (
        [("CAMPAIGNS_PER_KIND_DAY", {"user_id": "sam"})] if outcome == ONE_A_DAY else []
    )


def test_unsubscribing_from_a_campaign_turns_off_only_its_setting_and_counts_against_it(
    monkeypatch,
):
    turned_off, marked = [], []

    async def library_unsubscribe(user_id, settings):
        turned_off.append(settings)

    async def mark_unsubscribed(user_id, kind):
        marked.append((user_id, kind))

    monkeypatch.setattr(unsubscribe.library, "unsubscribe", library_unsubscribe)
    monkeypatch.setattr(bulk_recipients, "mark_unsubscribed", mark_unsubscribed)

    asyncio.run(unsubscribe.apply({"type": "promotions", "user_id": "ann"}))
    asyncio.run(unsubscribe.apply({"type": "digest", "user_id": "ann"}))

    assert turned_off[0] == ["promotions"]
    assert marked == [("ann", "promotions")]


def test_only_a_superadmin_reaches_campaigns(client, monkeypatch):
    monkeypatch.setenv("SUPERADMIN_EMAILS", "sam@prepza.dev")
    app.dependency_overrides[current_user] = lambda: User(
        uid="ann", email="ann@example.com", email_verified=True
    )

    assert client.get("/superadmin/campaigns").status_code == 404
    assert client.post(f"/superadmin/campaigns/{uuid.uuid4()}/send").status_code == 404

    app.dependency_overrides.clear()
