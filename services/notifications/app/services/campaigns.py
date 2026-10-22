# Campaigns as superadmins write them: in English, translated by generation, and changeable per
# language until they're sent.
import logging
import uuid

from fastapi import HTTPException, status
from prepza_common.constants import DEFAULT_LANGUAGE

from app.constants.bulk import BulkKind
from app.constants.campaigns import (
    ALREADY_SENT,
    COMPANIES_ONLY_NOTICES,
    LINK_NOT_ON_SITE,
    NEWS_BUTTON,
    NEWS_LINK,
    NO_BUTTON_TEXT,
    OWNERS_NEED_COMPANIES,
    AudienceGroup,
)
from app.integrations import companies, generation, library
from app.models.bulk import BulkSend
from app.models.campaigns import Campaign
from app.schemas.campaigns import (
    AudienceIn,
    CampaignIn,
    CampaignOut,
    CampaignRowOut,
    CampaignTexts,
    CompanyOut,
)
from app.storage import bulk_sends, campaigns

logger = logging.getLogger(__name__)

NOT_FOUND = "Not found"


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


def refused(outcome) -> None:
    """A storage answer that refuses: gone (None) or already sent."""
    if outcome is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND)

    if outcome == ALREADY_SENT:
        raise HTTPException(status.HTTP_409_CONFLICT, ALREADY_SENT)


async def send_to_translator(campaign_id: uuid.UUID) -> None:
    """Never raises: the campaign is saved first, and saving it again sends it again."""
    try:
        await generation.translate_campaign(str(campaign_id))
    except Exception:
        logger.exception("Couldn't send campaign %s to be translated", campaign_id)


async def companies_of(campaign: Campaign) -> list[CompanyOut]:
    """The companies an important notice goes to, by name, as chosen; those gone are left out."""
    if not campaign.company_ids:
        return []

    found = await companies.members([str(company_id) for company_id in campaign.company_ids])
    names = {company["id"]: company["name"] for company in found}

    return [
        CompanyOut(id=company_id, name=names[str(company_id)])
        for company_id in campaign.company_ids
        if str(company_id) in names
    ]


async def out(campaign: Campaign) -> CampaignOut:
    _, texts = await campaigns.get(campaign.id)
    row = await row_out(campaign, texts[DEFAULT_LANGUAGE]["subject"], len(texts))

    return CampaignOut(
        **row.model_dump(),
        link=campaign.link,
        groups=campaign.groups,
        editors_only=campaign.editors_only,
        companies=await companies_of(campaign),
        texts=texts,
    )


def status_of(send) -> str:
    if send is None:
        return "draft"

    if send.stopped_at:
        return "stopped"

    return "sent" if send.finished_at else "sending"


def row_of(
    campaign: Campaign, subject: str, languages: int, send: BulkSend | None, counts: dict | None
) -> CampaignRowOut:
    return CampaignRowOut(
        id=campaign.id,
        kind=campaign.kind,
        subject=subject,
        created_at=campaign.created_at,
        sent_at=campaign.sent_at,
        translated=languages > len(campaigns.OTHER_LANGUAGES),
        status=status_of(send),
        counts=counts if send and send.prepared_at else None,
    )


async def rows_out(rows: list[tuple[Campaign, str, int]]) -> list[CampaignRowOut]:
    """Each campaign with its send and the send's counts, read for all of them at once."""
    sent = [(campaign.kind, str(campaign.id)) for campaign, _, _ in rows if campaign.sent_at]
    sends = await bulk_sends.of_campaigns(sent)
    counts = await bulk_sends.counts([send.id for send in sends.values()]) if sends else {}
    out = []

    for campaign, subject, languages in rows:
        send = sends.get((campaign.kind, str(campaign.id))) if campaign.sent_at else None
        out.append(
            row_of(campaign, subject, languages, send, counts.get(send.id) if send else None)
        )

    return out


async def row_out(campaign: Campaign, subject: str, languages: int) -> CampaignRowOut:
    [row] = await rows_out([(campaign, subject, languages)])

    return row


async def list_campaigns(offset: int, limit: int) -> list[CampaignRowOut]:
    return await rows_out(await campaigns.list_campaigns(offset, limit))


async def get(campaign_id: uuid.UUID) -> CampaignOut:
    found = await campaigns.get(campaign_id)
    refused(found)

    return await out(found[0])


async def create(body: CampaignIn, user_id: str) -> CampaignOut:
    body = checked(body)
    campaign = await campaigns.create(fields_of(body), user_id, english_of(body))
    await send_to_translator(campaign.id)

    return await out(campaign)


async def from_news(news_id: uuid.UUID, user_id: str) -> CampaignOut:
    """A new product update made from a news post: its title, text and a button to it."""
    post = await library.news_post(str(news_id))

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


async def update(campaign_id: uuid.UUID, body: CampaignIn) -> CampaignOut:
    """A changed English text is translated again; a new kind, audience or link alone keeps the
    other languages."""
    body = checked(body)
    saved = await campaigns.update(campaign_id, fields_of(body), english_of(body))
    refused(saved)
    campaign, changed = saved

    if changed:
        await send_to_translator(campaign_id)

    return await out(campaign)


async def set_texts(campaign_id: uuid.UUID, language: str, body: CampaignTexts) -> CampaignOut:
    """One language's own wording; English is changed through update, which translates again."""
    if language == DEFAULT_LANGUAGE:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND)

    refused(await campaigns.set_texts(campaign_id, language, english_of(body)) or "ok")

    return await get(campaign_id)


async def remove(campaign_id: uuid.UUID) -> None:
    refused(await campaigns.remove(campaign_id) or "ok")
