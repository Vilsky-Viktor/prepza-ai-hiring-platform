"""Generation's `notification.campaign_translated`: the translations are saved with the English
they're of (an empty button as none); one that fails validation is dropped."""

import uuid

from event_pushes import push

from notifications.services import campaigns

CAMPAIGN = uuid.uuid4()
ENGLISH = {"subject": "New", "text": "One.", "button": None}


def test_a_campaigns_translations_are_saved_with_their_english(client, monkeypatch):
    saved = []

    async def save_translations(campaign_id, english, translations):
        saved.append((campaign_id, english, translations))

    monkeypatch.setattr(campaigns, "save_translations", save_translations)
    data = {
        "campaign_id": str(CAMPAIGN),
        **ENGLISH,
        "translations": {"de": {"subject": "Neu", "text": "Eins.", "button": ""}},
    }
    bad = {**data, "translations": {"xx": {"subject": "?", "text": "?"}}}

    codes = [
        client.post(
            "/internal/events", json=push("notification.campaign_translated", body)
        ).status_code
        for body in (data, bad)
    ]

    assert codes == [204, 204]
    assert saved == [
        (CAMPAIGN, ENGLISH, {"de": {"subject": "Neu", "text": "Eins.", "button": None}})
    ]
