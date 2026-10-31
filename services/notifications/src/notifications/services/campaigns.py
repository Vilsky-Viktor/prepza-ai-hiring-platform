# Campaigns as superadmins write them: in English, translated by generation (its translations come
# back as `notification.campaign_translated`), and changeable per language until they're sent.
import logging
import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from testee_common.config.constants import DEFAULT_LANGUAGE

from notifications.constants.bulk import BulkKind
from notifications.constants.campaigns import (
    ALREADY_SENT,
    COMPANIES_ONLY_NOTICES,
    LINK_NOT_ON_SITE,
    NEWS_BUTTON,
    NEWS_LINK,
    NO_BUTTON_TEXT,
    NOT_FOUND,
    OWNERS_NEED_COMPANIES,
    AudienceGroup,
)
from notifications.core.db import Session
from notifications.integrations import generation, site
from notifications.models.campaigns import Campaign
from notifications.repositories import campaigns
from notifications.schemas.campaigns import (
    AudienceIn,
    CampaignIn,
    CampaignOut,
    CampaignTexts,
)
from notifications.services.campaign_views import get, out, source

logger = logging.getLogger(__name__)


def english_of(body: CampaignTexts) -> dict:
    return {"subject": body.subject, "text": body.text, "button": body.button or None}


def checked_audience(body: AudienceIn) -> AudienceIn:
    """Owners and admins only, and some companies only, narrow the companies group; only an
    important notice goes to some companies only. Each group once."""
    members = AudienceGroup.MEMBERS in body.groups

    if body.editors_only and not members:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, OWNERS_NEED_COMPANIES)

    if body.company_ids and (body.kind != BulkKind.NOTICES or not members):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, COMPANIES_ONLY_NOTICES)

    return body.model_copy(
        update={
            "groups": list(dict.fromkeys(body.groups)),
            "company_ids": list(dict.fromkeys(body.company_ids)),
        }
    )


def checked(body: CampaignIn) -> CampaignIn:
    """The button opens a page on the site, and has a text when it has a link; the audience is
    one that can be chosen."""
    if body.link and (not body.link.startswith("/") or body.link.startswith("//")):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, LINK_NOT_ON_SITE)

    if body.link and not body.button:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, NO_BUTTON_TEXT)

    return checked_audience(body)


def fields_of(body: CampaignIn) -> dict:
    """The campaign's columns besides its texts."""
    return {
        "kind": body.kind,
        "groups": [str(group) for group in body.groups],
        "editors_only": body.editors_only,
        "company_ids": body.company_ids,
        "link": body.link or None,
    }


async def send_to_translator(campaign_id: uuid.UUID) -> None:
    """Sends the campaign's English texts and the languages it lacks to generation. Never
    raises: the campaign is saved first, and saving it again sends it again."""
    try:
        found = await source(campaign_id)
        await generation.translate_campaign(str(campaign_id), found.model_dump())
    except Exception:
        logger.exception("Couldn't send campaign %s to be translated", campaign_id)


async def create(body: CampaignIn, user_id: str) -> CampaignOut:
    body = checked(body)

    async with Session.begin() as session:
        campaign = await campaigns.create(session, fields_of(body), user_id, english_of(body))

    await send_to_translator(campaign.id)

    return await out(campaign)


async def from_news(news_id: uuid.UUID, user_id: str) -> CampaignOut:
    """A new product update made from a news post: its title, text and a button to it."""
    post = await site.news_post(str(news_id))

    if post is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND)

    body = CampaignIn(
        kind=BulkKind.UPDATES.value,
        subject=post["title"],
        text=post["text"],
        button=NEWS_BUTTON,
        link=NEWS_LINK.format(news_id=news_id),
    )

    return await create(body, user_id)


async def unsent(session: AsyncSession, campaign_id: uuid.UUID) -> Campaign:
    """The campaign, locked so it can't be sent meanwhile; 404 when it's gone, 409 once it's
    sent (raised inside the transaction, which saves nothing)."""
    campaign = await campaigns.lock(session, campaign_id)

    if campaign is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND)

    if campaign.sent_at is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, ALREADY_SENT)

    return campaign


async def update(campaign_id: uuid.UUID, body: CampaignIn) -> CampaignOut:
    """Saves the campaign as written in English, in one save. A changed English text deletes
    the other languages and is translated again; a new kind, audience or link alone keeps
    them."""
    body = checked(body)
    english = english_of(body)

    async with Session.begin() as session:
        campaign = await unsent(session, campaign_id)
        changed = await campaigns.english(session, campaign_id) != english

        if changed:
            await campaigns.replace_texts(session, campaign_id, english)

        campaign = await campaigns.change(session, campaign, fields_of(body))

    if changed:
        await send_to_translator(campaign_id)

    return await out(campaign)


async def set_texts(campaign_id: uuid.UUID, language: str, body: CampaignTexts) -> CampaignOut:
    """One language's own wording; English is changed through update, which translates again."""
    if language == DEFAULT_LANGUAGE:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND)

    async with Session.begin() as session:
        await unsent(session, campaign_id)
        await campaigns.set_texts(session, campaign_id, language, english_of(body))

    return await get(campaign_id)


async def save_translations(
    campaign_id: uuid.UUID, english: dict, translations: dict[str, dict]
) -> None:
    """Saves translations of the campaign as its English reads `english`; nothing when it
    changed since, was sent or is gone. A language that has texts already (edited by hand, or
    saved by an earlier run) keeps them."""
    others = {code: texts for code, texts in translations.items() if code != DEFAULT_LANGUAGE}

    async with Session.begin() as session:
        campaign = await campaigns.lock(session, campaign_id)

        if campaign is None or campaign.sent_at is not None:
            return

        if await campaigns.english(session, campaign_id) != english:
            return

        await campaigns.add_translations(session, campaign_id, others)


async def remove(campaign_id: uuid.UUID) -> None:
    """Deletes a campaign not sent yet; 409 for one that was. Safe to repeat."""
    async with Session.begin() as session:
        campaign = await campaigns.lock(session, campaign_id)

        if campaign is not None and campaign.sent_at is not None:
            raise HTTPException(status.HTTP_409_CONFLICT, ALREADY_SENT)

        await campaigns.remove(session, campaign_id)
