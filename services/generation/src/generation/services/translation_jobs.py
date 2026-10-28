# The jobs that translate a news post or a campaign into every language it lacks: each language
# goes in the next OpenAI batch at half price (services/batch_work.py), as nobody waits on it;
# until it's saved, readers see the English.
from uuid import UUID

from generation.constants.batch_work import BatchKind, BatchStep
from generation.integrations import notifications, site
from generation.services.batch_work import queue


async def translate_news(news_id: UUID) -> None:
    """Queues the post's translation into each language it lacks. Safe to repeat: a language
    already waiting isn't queued twice, and one translated since isn't missing any more."""
    source = await site.get_news_source(news_id)

    if source is None:
        return

    for language in source.missing:
        payload = {"source": source.model_dump(), "language": language}
        await queue(BatchKind.NEWS, news_id, BatchStep.TRANSLATE, payload, key=language)


async def translate_campaign(campaign_id: UUID) -> None:
    """Queues the campaign's translation into each language it lacks; nothing once it's sent or
    deleted. Safe to repeat, as the post's."""
    source = await notifications.get_campaign_source(campaign_id)

    if source is None:
        return

    for language in source.missing:
        payload = {"source": source.model_dump(), "language": language}
        await queue(BatchKind.CAMPAIGN, campaign_id, BatchStep.TRANSLATE, payload, key=language)
