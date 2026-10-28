import uuid
from datetime import UTC, datetime

from prepza_common.config.constants import DEFAULT_LANGUAGE, LANGUAGES
from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert

from notifications.constants.campaigns import ALREADY_SENT, CHANGED, ONE_A_DAY
from notifications.core.db import Session
from notifications.models.bulk import BulkSend
from notifications.models.campaigns import Campaign, CampaignText

# The languages a campaign is translated into.
OTHER_LANGUAGES = [code for code in LANGUAGES if code != DEFAULT_LANGUAGE]


def as_texts(row: CampaignText) -> dict:
    return {"subject": row.subject, "text": row.text, "button": row.button}


async def create(fields: dict, created_by: str, english: dict) -> Campaign:
    """`fields`: its kind, audience and link."""
    async with Session() as session:
        campaign = Campaign(id=uuid.uuid4(), created_by=created_by, **fields)
        session.add(campaign)
        await session.flush()
        session.add(CampaignText(campaign_id=campaign.id, language=DEFAULT_LANGUAGE, **english))
        await session.commit()
        await session.refresh(campaign)

        return campaign


async def get(campaign_id: uuid.UUID) -> tuple[Campaign, dict[str, dict]] | None:
    """The campaign and its texts by language; None when there's no such campaign."""
    async with Session() as session:
        campaign = await session.get(Campaign, campaign_id)

        if campaign is None:
            return None

        rows = await session.scalars(
            select(CampaignText).where(CampaignText.campaign_id == campaign_id)
        )

        return campaign, {row.language: as_texts(row) for row in rows}


async def list_campaigns(offset: int, limit: int) -> list[tuple[Campaign, str, int]]:
    """Newest first, each with its English subject and how many languages it has."""
    languages = (
        select(func.count())
        .where(CampaignText.campaign_id == Campaign.id)
        .correlate(Campaign)
        .scalar_subquery()
    )
    query = (
        select(Campaign, CampaignText.subject, languages)
        .join(
            CampaignText,
            (CampaignText.campaign_id == Campaign.id) & (CampaignText.language == DEFAULT_LANGUAGE),
        )
        .order_by(Campaign.created_at.desc(), Campaign.id.desc())
        .offset(offset)
        .limit(limit)
    )

    async with Session() as session:
        return [tuple(row) for row in await session.execute(query)]


async def update(
    campaign_id: uuid.UUID, fields: dict, english: dict
) -> tuple[Campaign, bool] | str | None:
    """Saves the campaign as written in English (`fields`: its kind, audience and link), and
    whether its texts changed: then the other
    languages are deleted, to be translated again. ALREADY_SENT once it's sent (the row is
    locked, so it can't be sent meanwhile); None when it's gone."""
    async with Session() as session:
        campaign = await session.get(Campaign, campaign_id, with_for_update=True)

        if campaign is None:
            return None

        if campaign.sent_at is not None:
            return ALREADY_SENT

        current = await session.get(CampaignText, (campaign_id, DEFAULT_LANGUAGE))
        changed = as_texts(current) != english

        if changed:
            await session.execute(
                delete(CampaignText).where(CampaignText.campaign_id == campaign_id)
            )
            session.add(CampaignText(campaign_id=campaign_id, language=DEFAULT_LANGUAGE, **english))

        for name, value in fields.items():
            setattr(campaign, name, value)

        await session.commit()
        await session.refresh(campaign)

        return campaign, changed


async def set_texts(campaign_id: uuid.UUID, language: str, texts: dict) -> str | None:
    """A superadmin's own wording in one other language. ALREADY_SENT once it's sent."""
    async with Session() as session:
        campaign = await session.get(Campaign, campaign_id, with_for_update=True)

        if campaign is not None and campaign.sent_at is not None:
            return ALREADY_SENT

        if campaign is not None:
            await session.execute(
                insert(CampaignText)
                .values(campaign_id=campaign_id, language=language, **texts)
                .on_conflict_do_update(
                    index_elements=[CampaignText.campaign_id, CampaignText.language], set_=texts
                )
            )
            await session.commit()

    return None


async def save_translations(
    campaign_id: uuid.UUID, english: dict, translations: dict[str, dict]
) -> None:
    """Saves translations of the campaign as its English reads `english`; nothing when it
    changed since, was sent or is gone. A language that has texts already (edited by hand, or
    saved by an earlier run) keeps them."""
    async with Session() as session:
        campaign = await session.get(Campaign, campaign_id, with_for_update=True)
        current = await session.get(CampaignText, (campaign_id, DEFAULT_LANGUAGE))

        if campaign is None or campaign.sent_at is not None or as_texts(current) != english:
            return

        for language, texts in translations.items():
            if language == DEFAULT_LANGUAGE:
                continue

            await session.execute(
                insert(CampaignText)
                .values(campaign_id=campaign_id, language=language, **texts)
                .on_conflict_do_nothing()
            )

        await session.commit()


async def remove(campaign_id: uuid.UUID) -> str | None:
    """Deletes a campaign not sent yet; ALREADY_SENT for one that was. Safe to repeat."""
    async with Session() as session:
        campaign = await session.get(Campaign, campaign_id, with_for_update=True)

        if campaign is not None and campaign.sent_at is not None:
            return ALREADY_SENT

        await session.execute(delete(Campaign).where(Campaign.id == campaign_id))
        await session.commit()

    return None


async def mark_sent(
    campaign_id: uuid.UUID, kind: str, asked_by: str, per_day: int
) -> uuid.UUID | str | None:
    """Marks the campaign sent and starts its bulk send, in one transaction; the send's id.
    ALREADY_SENT when it was, CHANGED when it's no longer of the `kind` its checks were for,
    ONE_A_DAY when `per_day` of its kind went out today (UTC), None when it's gone. Campaigns of
    one kind are sent one at a time (a lock), so two at once can't both pass the check."""
    async with Session() as session:
        campaign = await session.get(Campaign, campaign_id, with_for_update=True)

        if campaign is None:
            return None

        if campaign.sent_at is not None:
            return ALREADY_SENT

        if campaign.kind != kind:
            return CHANGED

        await session.execute(
            select(func.pg_advisory_xact_lock(func.hashtext(f"campaigns:{campaign.kind}")))
        )
        midnight = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        today = await session.scalar(
            select(func.count()).where(Campaign.kind == campaign.kind, Campaign.sent_at >= midnight)
        )

        if today >= per_day:
            return ONE_A_DAY

        campaign.sent_at = datetime.now(UTC)
        send = BulkSend(
            id=uuid.uuid4(), kind=campaign.kind, about=str(campaign_id), asked_by=asked_by
        )
        session.add(send)
        await session.commit()

        return send.id
