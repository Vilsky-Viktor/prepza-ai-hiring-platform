# A news post or a campaign, as site or notifications sent it, queued for translation into every
# language it lacks: each language goes in the next OpenAI batch at half price
# (services/batch_work.py), as nobody waits on it; until it's saved, readers see the English.
from uuid import UUID

from generation.constants.batch_work import BatchKind, BatchStep
from generation.schemas.campaigns import CampaignSource
from generation.schemas.news import NewsSource
from generation.services.batch_work import queue


async def translate_news(news_id: UUID, source: NewsSource) -> None:
    """Queues the post's translation into each language it lacks, as site sent it. Safe to
    repeat: a language already waiting isn't queued twice, and one translated since isn't
    missing any more."""
    for language in source.missing:
        payload = {"source": source.model_dump(), "language": language}
        await queue(BatchKind.NEWS, news_id, BatchStep.TRANSLATE, payload, key=language)


async def translate_campaign(campaign_id: UUID, source: CampaignSource) -> None:
    """Queues the campaign's translation into each language it lacks (none once it's sent), as
    notifications sent it. Safe to repeat, as the post's."""
    for language in source.missing:
        payload = {"source": source.model_dump(), "language": language}
        await queue(BatchKind.CAMPAIGN, campaign_id, BatchStep.TRANSLATE, payload, key=language)
