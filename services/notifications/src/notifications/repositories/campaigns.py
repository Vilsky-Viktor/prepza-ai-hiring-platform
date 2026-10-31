import uuid
from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from testee_common.config.constants import DEFAULT_LANGUAGE, LANGUAGES

from notifications.models.campaigns import Campaign, CampaignText

# The languages a campaign is translated into.
OTHER_LANGUAGES = [code for code in LANGUAGES if code != DEFAULT_LANGUAGE]


def as_texts(row: CampaignText) -> dict:
    return {"subject": row.subject, "text": row.text, "button": row.button}


async def create(session: AsyncSession, fields: dict, created_by: str, english: dict) -> Campaign:
    """`fields`: its kind, audience and link."""
    campaign = Campaign(id=uuid.uuid4(), created_by=created_by, **fields)
    session.add(campaign)
    await session.flush()
    session.add(CampaignText(campaign_id=campaign.id, language=DEFAULT_LANGUAGE, **english))
    await session.flush()
    await session.refresh(campaign)

    return campaign


async def get(
    session: AsyncSession, campaign_id: uuid.UUID
) -> tuple[Campaign, dict[str, dict]] | None:
    """The campaign and its texts by language; None when there's no such campaign."""
    campaign = await session.get(Campaign, campaign_id)

    if campaign is None:
        return None

    rows = await session.scalars(
        select(CampaignText).where(CampaignText.campaign_id == campaign_id)
    )

    return campaign, {row.language: as_texts(row) for row in rows}


async def list_campaigns(
    session: AsyncSession, offset: int, limit: int
) -> list[tuple[Campaign, str, int]]:
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

    return [tuple(row) for row in await session.execute(query)]


async def lock(session: AsyncSession, campaign_id: uuid.UUID) -> Campaign | None:
    """The campaign, locked until the transaction ends (so it can't be sent meanwhile)."""
    return await session.get(Campaign, campaign_id, with_for_update=True, populate_existing=True)


async def english(session: AsyncSession, campaign_id: uuid.UUID) -> dict | None:
    """Its texts as written in English."""
    row = await session.get(CampaignText, (campaign_id, DEFAULT_LANGUAGE))

    return as_texts(row) if row else None


async def replace_texts(session: AsyncSession, campaign_id: uuid.UUID, english: dict) -> None:
    """New English texts: the other languages go, to be translated again."""
    await session.execute(delete(CampaignText).where(CampaignText.campaign_id == campaign_id))
    session.add(CampaignText(campaign_id=campaign_id, language=DEFAULT_LANGUAGE, **english))
    await session.flush()


async def change(session: AsyncSession, campaign: Campaign, fields: dict) -> Campaign:
    """`fields`: its kind, audience and link."""
    for name, value in fields.items():
        setattr(campaign, name, value)

    await session.flush()
    await session.refresh(campaign)

    return campaign


async def set_texts(
    session: AsyncSession, campaign_id: uuid.UUID, language: str, texts: dict
) -> None:
    """One language's texts, replacing those it had."""
    await session.execute(
        insert(CampaignText)
        .values(campaign_id=campaign_id, language=language, **texts)
        .on_conflict_do_update(
            index_elements=[CampaignText.campaign_id, CampaignText.language], set_=texts
        )
    )


async def add_translations(
    session: AsyncSession, campaign_id: uuid.UUID, translations: dict[str, dict]
) -> None:
    """Texts in other languages; a language that has texts already keeps them."""
    for language, texts in translations.items():
        await session.execute(
            insert(CampaignText)
            .values(campaign_id=campaign_id, language=language, **texts)
            .on_conflict_do_nothing()
        )


async def remove(session: AsyncSession, campaign_id: uuid.UUID) -> None:
    await session.execute(delete(Campaign).where(Campaign.id == campaign_id))


async def lock_kind(session: AsyncSession, kind: str) -> None:
    """Campaigns of one kind are sent one at a time, until the transaction ends."""
    await session.execute(select(func.pg_advisory_xact_lock(func.hashtext(f"campaigns:{kind}"))))


async def sent_since(session: AsyncSession, kind: str, since: datetime) -> int:
    """How many campaigns of the kind were sent since then."""
    return await session.scalar(
        select(func.count()).where(Campaign.kind == kind, Campaign.sent_at >= since)
    )


async def mark_sent(session: AsyncSession, campaign: Campaign, now: datetime) -> None:
    campaign.sent_at = now
    await session.flush()
