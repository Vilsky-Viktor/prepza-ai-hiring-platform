# Sending a campaign: who it would reach, a preview and a test to the superadmin, then the bulk
# send to everyone, which can be stopped.
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from testee_common.auth.user import User
from testee_common.i18n.i18n import TemplateError
from testee_common.limits.limits import limit, record_hit
from testee_common.limits.rate_limit import until_tomorrow

from notifications.config import settings
from notifications.constants.bulk import OPTIONAL_KINDS, BulkKind
from notifications.constants.campaigns import (
    ALREADY_SENT,
    CHANGED,
    NOT_ACKNOWLEDGED,
    NOT_FOUND,
    NOT_SENT,
    ONE_A_DAY,
)
from notifications.core.db import Session
from notifications.helpers.campaign_emails import campaign_email
from notifications.helpers.unsubscribe import address_hash
from notifications.integrations import accounts
from notifications.integrations.redis import get_redis
from notifications.repositories import bulk_sends, campaigns, suppressed
from notifications.schemas.campaigns import AudienceIn, CampaignOut, PreviewOut
from notifications.services import bulk, delivery
from notifications.services.audiences import campaign_audience, everyone
from notifications.services.bulk import prepare_now
from notifications.services.campaign_views import get, read
from notifications.services.campaigns import checked_audience

# How many of each kind may go out a day.
DAY_LIMITS = {BulkKind.NOTICES: "NOTICES_PER_DAY"}


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
    people = await accounts.recipients(await everyone(campaign_audience(chosen)))

    if chosen.kind in OPTIONAL_KINDS:
        people = [person for person in people if person["preferences"].get(chosen.kind)]

    async with Session() as session:
        hashes = await suppressed.among(
            session, [address_hash(person["email"]) for person in people]
        )

    return sum(address_hash(person["email"]) not in hashes for person in people)


async def recipients_count(campaign_id: uuid.UUID) -> int:
    """Who the campaign would reach now (reachable())."""
    campaign, _ = await read(campaign_id)
    chosen = AudienceIn(
        kind=campaign.kind,
        groups=campaign.groups,
        editors_only=campaign.editors_only,
        company_ids=campaign.company_ids,
    )

    return await reachable(chosen)


async def preview(campaign_id: uuid.UUID, language: str, user: User) -> PreviewOut:
    """The email as a user in `language` gets it, addressed to the superadmin."""
    campaign, texts = await read(campaign_id)
    recipient = {"user_id": user.uid, "email": user.email, "language": language}
    email = email_of(campaign, texts, recipient)

    return PreviewOut(subject=email.subject, html=email.html)


async def send_test(campaign_id: uuid.UUID, language: str, user: User) -> None:
    """The email in `language` to the superadmin's own address; each test is sent."""
    campaign, texts = await read(campaign_id)
    recipient = {"user_id": user.uid, "email": user.email, "language": language}
    await delivery.send(email_of(campaign, texts, recipient), f"campaign-test/{uuid.uuid4()}")


async def send(campaign_id: uuid.UUID, user_id: str, acknowledged: bool) -> CampaignOut:
    """Starts the campaign at once: its recipients are worked out now, and the sending hours'
    runs email them. Refused when it was sent, when an important notice wasn't confirmed as one
    (`acknowledged`), or when its kind's day limit went out today (CAMPAIGNS_PER_KIND_DAY, or
    NOTICES_PER_DAY)."""
    campaign, _ = await read(campaign_id)

    if campaign.kind == BulkKind.NOTICES and not acknowledged:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, NOT_ACKNOWLEDGED)

    name = DAY_LIMITS.get(campaign.kind, "CAMPAIGNS_PER_KIND_DAY")
    per_day = await limit(get_redis(), name)

    if not await mark_sent(campaign_id, campaign.kind, user_id, per_day):
        await record_hit(name, user_id=user_id)

        # The day's limit: waiting until tomorrow frees it.
        raise TemplateError(
            status.HTTP_429_TOO_MANY_REQUESTS, ONE_A_DAY, headers=until_tomorrow(), limit=per_day
        )

    await prepare_now(campaign.kind, str(campaign_id))

    return await get(campaign_id)


async def mark_sent(campaign_id: uuid.UUID, kind: str, asked_by: str, per_day: int) -> bool:
    """Marks the campaign sent and starts its bulk send, in one save; False when `per_day` of
    its kind went out today (UTC), saving nothing. 404 when it's gone, 409 when it was sent or
    is no longer of the `kind` its checks were for. Campaigns of one kind are sent one at a time
    (a lock), so two at once can't both pass the check."""
    now = datetime.now(UTC)
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)

    async with Session.begin() as session:
        campaign = await campaigns.lock(session, campaign_id)

        if campaign is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND)

        if campaign.sent_at is not None:
            raise HTTPException(status.HTTP_409_CONFLICT, ALREADY_SENT)

        if campaign.kind != kind:
            raise HTTPException(status.HTTP_409_CONFLICT, CHANGED)

        await campaigns.lock_kind(session, kind)

        if await campaigns.sent_since(session, kind, midnight) >= per_day:
            return False

        await campaigns.mark_sent(session, campaign, now)
        await bulk_sends.add(session, kind, str(campaign_id), asked_by)

    return True


async def stop(campaign_id: uuid.UUID) -> CampaignOut:
    """Its remaining recipients aren't sent it."""
    campaign, _ = await read(campaign_id)

    async with Session() as session:
        send_row = await bulk_sends.get(session, campaign.kind, str(campaign_id))

    if send_row is None:
        raise HTTPException(status.HTTP_409_CONFLICT, NOT_SENT)

    await bulk.stop(send_row.id)

    return await get(campaign_id)
