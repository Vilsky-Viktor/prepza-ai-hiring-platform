import logging
from uuid import UUID

from fastapi import APIRouter, status
from testee_common.auth.superadmin import SuperadminUser
from testee_common.auth.user import Language
from testee_common.db.paging import PageParams

from notifications.schemas.campaigns import (
    AudienceIn,
    CampaignIn,
    CampaignOut,
    CampaignRowOut,
    CampaignTexts,
    PreviewOut,
    RecipientsOut,
    SendIn,
)
from notifications.services import campaign_sends, campaign_views, campaigns

logger = logging.getLogger(__name__)

# The admin zone's Campaigns tab: product updates and offers to the users who chose them, and
# important notices to everyone they concern, written in English, translated, checked and sent
# at once. Everyone else gets "not found".
router = APIRouter(prefix="/superadmin/campaigns", tags=["superadmin"])


@router.get("")
async def list_campaigns(superadmin: SuperadminUser, page: PageParams) -> list[CampaignRowOut]:
    """Newest first, with each sent one's counts."""
    return await campaign_views.list_campaigns(page.offset, page.limit)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_campaign(body: CampaignIn, superadmin: SuperadminUser) -> CampaignOut:
    return await campaigns.create(body, superadmin.uid)


@router.post("/recipients")
async def count_audience(body: AudienceIn, superadmin: SuperadminUser) -> RecipientsOut:
    """Who a campaign of that kind and audience would reach now, as the dialog's choice
    changes."""
    return RecipientsOut(count=await campaign_sends.reachable(body))


@router.post("/from-news/{news_id}", status_code=status.HTTP_201_CREATED)
async def campaign_from_news(news_id: UUID, superadmin: SuperadminUser) -> CampaignOut:
    """A new product update with the news post's title, text and a button to it."""
    return await campaigns.from_news(news_id, superadmin.uid)


@router.get("/{campaign_id}")
async def get_campaign(campaign_id: UUID, superadmin: SuperadminUser) -> CampaignOut:
    return await campaign_views.get(campaign_id)


@router.put("/{campaign_id}")
async def update_campaign(
    campaign_id: UUID, body: CampaignIn, superadmin: SuperadminUser
) -> CampaignOut:
    """Until it's sent; a changed English text is translated again."""
    return await campaigns.update(campaign_id, body)


@router.put("/{campaign_id}/texts/{language}")
async def set_campaign_texts(
    campaign_id: UUID, language: Language, body: CampaignTexts, superadmin: SuperadminUser
) -> CampaignOut:
    """One other language's own wording, until it's sent."""
    return await campaigns.set_texts(campaign_id, language, body)


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(campaign_id: UUID, superadmin: SuperadminUser) -> None:
    """Only one not sent yet."""
    await campaigns.remove(campaign_id)


@router.get("/{campaign_id}/recipients")
async def count_recipients(campaign_id: UUID, superadmin: SuperadminUser) -> RecipientsOut:
    return RecipientsOut(count=await campaign_sends.recipients_count(campaign_id))


@router.get("/{campaign_id}/preview")
async def preview_campaign(
    campaign_id: UUID, superadmin: SuperadminUser, language: Language = "en"
) -> PreviewOut:
    """The email as a user in that language gets it."""
    return await campaign_sends.preview(campaign_id, language, superadmin)


@router.post("/{campaign_id}/test", status_code=status.HTTP_204_NO_CONTENT)
async def send_test(
    campaign_id: UUID, superadmin: SuperadminUser, language: Language = "en"
) -> None:
    """The email in that language to the superadmin's own address."""
    await campaign_sends.send_test(campaign_id, language, superadmin)


@router.post("/{campaign_id}/send")
async def send_campaign(
    campaign_id: UUID, superadmin: SuperadminUser, body: SendIn | None = None
) -> CampaignOut:
    """Starts it at once; it can't be changed after. At most one of each kind a day; an
    important notice only once confirmed as one."""
    acknowledged = body is not None and body.acknowledged
    sent = await campaign_sends.send(campaign_id, superadmin.uid, acknowledged)
    logger.warning(
        "Superadmin %s sent campaign %s (%s, to %s)",
        superadmin.uid,
        campaign_id,
        sent.kind,
        ", ".join(sent.groups) or "everyone",
    )

    return sent


@router.post("/{campaign_id}/stop")
async def stop_campaign(campaign_id: UUID, superadmin: SuperadminUser) -> CampaignOut:
    """Its remaining recipients aren't sent it."""
    stopped = await campaign_sends.stop(campaign_id)
    logger.warning("Superadmin %s stopped campaign %s", superadmin.uid, campaign_id)

    return stopped
