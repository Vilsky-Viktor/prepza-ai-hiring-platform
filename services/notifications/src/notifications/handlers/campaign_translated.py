from prepza_common.events.campaigns import CampaignTranslated

from notifications.services import campaigns


async def handle(data: dict, event_id: str) -> None:
    """Generation translated a campaign: saved while it still reads as the English translated and
    isn't sent; a language that has texts already keeps them, so a redelivery saves nothing
    twice, and a late translation of an older text is dropped."""
    event = CampaignTranslated.model_validate(data)
    english = {"subject": event.subject, "text": event.text, "button": event.button}
    translations = {
        language: {"subject": item.subject, "text": item.text, "button": item.button or None}
        for language, item in event.translations.items()
    }
    await campaigns.save_translations(event.campaign_id, english, translations)
