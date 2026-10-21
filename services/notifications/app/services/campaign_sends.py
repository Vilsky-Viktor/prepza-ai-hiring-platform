# Sending a campaign: who it would reach, a preview and a test to the superadmin, then the bulk
# send to everyone, which can be stopped.
import uuid

from fastapi import HTTPException, status
from prepza_common.i18n import TemplateError
from prepza_common.limits import limit, record_hit
from prepza_common.rate_limit import until_tomorrow
from prepza_common.user import User

from app.config.settings import settings
from app.constants.campaigns import ALREADY_SENT, NOT_SENT, ONE_A_DAY
from app.helpers.campaign_emails import campaign_email
from app.helpers.unsubscribe import address_hash
from app.integrations import library
from app.integrations.redis import get_redis
from app.schemas.campaigns import CampaignOut, PreviewOut
from app.services import delivery
from app.services.bulk import prepare_now
from app.services.bulk_content import audience
from app.services.campaigns import NOT_FOUND, get, refused
from app.storage import bulk_sends, campaigns, suppressed


async def found(campaign_id: uuid.UUID):
    """The campaign and its texts by language; 404 when there's none."""
    result = await campaigns.get(campaign_id)
    refused(result)

    return result


def email_of(campaign, texts: dict, recipient: dict):
    return campaign_email(
        campaign.kind,
        recipient,
        texts,
        campaign.link,
        settings.site_url,
        settings.email_link_secret,
    )


async def recipients_count(campaign_id: uuid.UUID) -> int:
    """Users who'd get it now: its setting on, an address, not suppressed."""
    campaign, _ = await found(campaign_id)
    people = await library.recipients(await audience(campaign.kind))
    reachable = [person for person in people if person["preferences"].get(campaign.kind)]
    hashes = await suppressed.among([address_hash(person["email"]) for person in reachable])

    return sum(address_hash(person["email"]) not in hashes for person in reachable)


async def preview(campaign_id: uuid.UUID, language: str, user: User) -> PreviewOut:
    """The email as a user in `language` gets it, addressed to the superadmin."""
    campaign, texts = await found(campaign_id)
    recipient = {"user_id": user.uid, "email": user.email, "language": language}
    email = email_of(campaign, texts, recipient)

    return PreviewOut(subject=email.subject, html=email.html)


async def send_test(campaign_id: uuid.UUID, language: str, user: User) -> None:
    """The email in `language` to the superadmin's own address; each test is sent."""
    campaign, texts = await found(campaign_id)
    recipient = {"user_id": user.uid, "email": user.email, "language": language}
    await delivery.send(email_of(campaign, texts, recipient), f"campaign-test/{uuid.uuid4()}")


async def send(campaign_id: uuid.UUID, user_id: str) -> CampaignOut:
    """Starts the campaign at once: its recipients are worked out now, and the sending hours'
    runs email them. Refused when it was sent, or the CAMPAIGNS_PER_KIND_DAY limit of its kind
    went out today."""
    per_day = await limit(get_redis(), "CAMPAIGNS_PER_KIND_DAY")
    outcome = await campaigns.mark_sent(campaign_id, user_id, per_day)

    if outcome is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND)

    if outcome == ALREADY_SENT:
        raise HTTPException(status.HTTP_409_CONFLICT, outcome)

    if outcome == ONE_A_DAY:
        await record_hit("CAMPAIGNS_PER_KIND_DAY", user_id=user_id)

        # The day's limit: waiting until tomorrow frees it.
        raise TemplateError(
            status.HTTP_429_TOO_MANY_REQUESTS, ONE_A_DAY, headers=until_tomorrow(), limit=per_day
        )

    campaign, _ = await found(campaign_id)
    await prepare_now(campaign.kind, str(campaign_id))

    return await get(campaign_id)


async def stop(campaign_id: uuid.UUID) -> CampaignOut:
    """Its remaining recipients aren't sent it."""
    campaign, _ = await found(campaign_id)
    send_row = await bulk_sends.get(campaign.kind, str(campaign_id))

    if send_row is None:
        raise HTTPException(status.HTTP_409_CONFLICT, NOT_SENT)

    await bulk_sends.stop(send_row.id)

    return await get(campaign_id)
