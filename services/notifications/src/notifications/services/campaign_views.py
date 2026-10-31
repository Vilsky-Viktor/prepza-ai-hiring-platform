# Campaigns as superadmins see them: each with its send's state and counts, its texts by
# language and the companies an important notice goes to.
import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from testee_common.config.constants import DEFAULT_LANGUAGE

from notifications.constants.campaigns import NOT_FOUND
from notifications.core.db import Session
from notifications.integrations import companies
from notifications.models.bulk import BulkSend
from notifications.models.campaigns import Campaign
from notifications.repositories import bulk_sends, campaigns
from notifications.schemas.campaigns import (
    CampaignOut,
    CampaignRowOut,
    CampaignSourceOut,
    CompanyOut,
)


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
    async with Session() as session:
        _, texts = await campaigns.get(session, campaign.id)
        [row] = await rows_out(
            session, [(campaign, texts[DEFAULT_LANGUAGE]["subject"], len(texts))]
        )

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


async def rows_out(
    session: AsyncSession, rows: list[tuple[Campaign, str, int]]
) -> list[CampaignRowOut]:
    """Each campaign with its send and the send's counts, read for all of them at once."""
    sent = [(campaign.kind, str(campaign.id)) for campaign, _, _ in rows if campaign.sent_at]
    sends = await bulk_sends.of_campaigns(session, sent)
    counts = await bulk_sends.counts(session, [send.id for send in sends.values()]) if sends else {}
    out = []

    for campaign, subject, languages in rows:
        send = sends.get((campaign.kind, str(campaign.id))) if campaign.sent_at else None
        out.append(
            row_of(campaign, subject, languages, send, counts.get(send.id) if send else None)
        )

    return out


async def list_campaigns(offset: int, limit: int) -> list[CampaignRowOut]:
    async with Session() as session:
        return await rows_out(session, await campaigns.list_campaigns(session, offset, limit))


async def read(campaign_id: uuid.UUID) -> tuple[Campaign, dict[str, dict]]:
    """The campaign and its texts by language; 404 when there's none."""
    async with Session() as session:
        found = await campaigns.get(session, campaign_id)

    if found is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND)

    return found


async def get(campaign_id: uuid.UUID) -> CampaignOut:
    campaign, _ = await read(campaign_id)

    return await out(campaign)


async def source(campaign_id: uuid.UUID) -> CampaignSourceOut:
    """Its English texts and the languages it lacks; none once it's sent."""
    campaign, texts = await read(campaign_id)
    missing = [code for code in campaigns.OTHER_LANGUAGES if code not in texts]

    return CampaignSourceOut(**texts[DEFAULT_LANGUAGE], missing=[] if campaign.sent_at else missing)
