# Sending a campaign: who it would reach, a preview and a test to the superadmin, then the bulk
# send to everyone, which can be stopped.
import uuid

from fastapi import HTTPException, status
from prepza_common.auth.user import User
from prepza_common.i18n.i18n import TemplateError
from prepza_common.limits.limits import limit, record_hit
from prepza_common.limits.rate_limit import until_tomorrow

from app.config.settings import settings
from app.constants.bulk import OPTIONAL_KINDS, BulkKind
from app.constants.campaigns import ALREADY_SENT, CHANGED, NOT_ACKNOWLEDGED, NOT_SENT, ONE_A_DAY
from app.helpers.campaign_emails import campaign_email
from app.helpers.unsubscribe import address_hash
from app.integrations import library
from app.integrations.redis import get_redis
from app.schemas.campaigns import AudienceIn, CampaignOut, PreviewOut
from app.services import delivery
from app.services.audiences import campaign_audience, everyone
from app.services.bulk import prepare_now
from app.services.campaigns import NOT_FOUND, checked_audience, get, refused
from app.storage import bulk_sends, campaigns, suppressed

# How many of each kind may go out a day.
DAY_LIMITS = {BulkKind.NOTICES: "NOTICES_PER_DAY"}


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


async def reachable(chosen: AudienceIn) -> int:
    """Users of the audience who'd get it now, each once: an address, not suppressed, and for
    an optional kind its setting on."""
    chosen = checked_audience(chosen)
    people = await library.recipients(await everyone(campaign_audience(chosen)))

    if chosen.kind in OPTIONAL_KINDS:
        people = [person for person in people if person["preferences"].get(chosen.kind)]

    hashes = await suppressed.among([address_hash(person["email"]) for person in people])

    return sum(address_hash(person["email"]) not in hashes for person in people)


async def recipients_count(campaign_id: uuid.UUID) -> int:
    """Who the campaign would reach now (reachable())."""
    campaign, _ = await found(campaign_id)
    chosen = AudienceIn(
        kind=campaign.kind,
        groups=campaign.groups,
        editors_only=campaign.editors_only,
        company_ids=campaign.company_ids,
    )

    return await reachable(chosen)


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


async def send(campaign_id: uuid.UUID, user_id: str, acknowledged: bool) -> CampaignOut:
    """Starts the campaign at once: its recipients are worked out now, and the sending hours'
    runs email them. Refused when it was sent, when an important notice wasn't confirmed as one
    (`acknowledged`), or when its kind's day limit went out today (CAMPAIGNS_PER_KIND_DAY, or
    NOTICES_PER_DAY)."""
    campaign, _ = await found(campaign_id)

    if campaign.kind == BulkKind.NOTICES and not acknowledged:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, NOT_ACKNOWLEDGED)

    name = DAY_LIMITS.get(campaign.kind, "CAMPAIGNS_PER_KIND_DAY")
    per_day = await limit(get_redis(), name)
    outcome = await campaigns.mark_sent(campaign_id, campaign.kind, user_id, per_day)

    if outcome is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND)

    if outcome in (ALREADY_SENT, CHANGED):
        raise HTTPException(status.HTTP_409_CONFLICT, outcome)

    if outcome == ONE_A_DAY:
        await record_hit(name, user_id=user_id)

        # The day's limit: waiting until tomorrow frees it.
        raise TemplateError(
            status.HTTP_429_TOO_MANY_REQUESTS, ONE_A_DAY, headers=until_tomorrow(), limit=per_day
        )

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
