import uuid

from prepza_common.config.constants import DEFAULT_LANGUAGE, LANGUAGES
from prepza_common.events.news import NewsTranslation as NewsTranslationIn
from prepza_common.events.notifications import NEWS_WITHDRAWN
from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from site_content.constants.news import NEWS_RESEND_BATCH
from site_content.models.news import News, NewsTranslation
from site_content.repositories import outbox
from site_content.schemas.news import NewsIn

# Newest first; posts of one day by when they were written.
NEWEST_FIRST = (News.published_on.desc(), News.created_at.desc(), News.id.desc())
# The languages a post is translated into.
OTHER_LANGUAGES = [code for code in LANGUAGES if code != DEFAULT_LANGUAGE]


async def list_news(
    session: AsyncSession, language: str, offset: int, limit: int
) -> list[tuple[News, str, str]]:
    """Posts with their title and text in `language`, or in English while it has no
    translation."""
    query = (
        select(
            News,
            func.coalesce(NewsTranslation.title, News.title),
            func.coalesce(NewsTranslation.text, News.text),
        )
        .outerjoin(
            NewsTranslation,
            (NewsTranslation.news_id == News.id) & (NewsTranslation.language == language),
        )
        .order_by(*NEWEST_FIRST)
        .offset(offset)
        .limit(limit)
    )

    return [tuple(row) for row in await session.execute(query)]


async def list_with_counts(
    session: AsyncSession, offset: int, limit: int
) -> list[tuple[News, int]]:
    """Posts with how many translations each has, for the admin zone."""
    counts = (
        select(func.count())
        .where(NewsTranslation.news_id == News.id)
        .correlate(News)
        .scalar_subquery()
    )
    query = select(News, counts).order_by(*NEWEST_FIRST).offset(offset).limit(limit)

    return [tuple(row) for row in await session.execute(query)]


async def get(session: AsyncSession, news_id: uuid.UUID) -> News | None:
    return await session.get(News, news_id)


async def create(session: AsyncSession, post: NewsIn) -> News:
    row = News(id=uuid.uuid4(), **post.model_dump())
    session.add(row)
    await session.flush()
    await session.refresh(row)

    return row


async def lock(session: AsyncSession, news_id: uuid.UUID) -> News | None:
    """The post, locked until the transaction ends, so an edit and a translation's save can't
    cross."""
    return await session.get(News, news_id, with_for_update=True)


async def clear_translations(session: AsyncSession, news_id: uuid.UUID) -> None:
    await session.execute(delete(NewsTranslation).where(NewsTranslation.news_id == news_id))


async def save(session: AsyncSession, row: News, post: NewsIn) -> News:
    row.title, row.text, row.published_on = post.title, post.text, post.published_on
    await session.flush()
    await session.refresh(row)

    return row


async def remove(session: AsyncSession, news_id: uuid.UUID) -> None:
    """Deletes the post with its translations, and its notification goes too (NEWS_WITHDRAWN,
    in the same transaction); safe to repeat."""
    removed = await session.scalar(delete(News).where(News.id == news_id).returning(News.id))

    if removed is not None:
        outbox.add(session, NEWS_WITHDRAWN, {"news_id": str(news_id)})


async def titles(session: AsyncSession, news_ids: list[uuid.UUID], language: str) -> dict[str, str]:
    """The posts' titles in `language`, in English where it has no translation; deleted posts
    are left out."""
    query = (
        select(News.id, func.coalesce(NewsTranslation.title, News.title))
        .outerjoin(
            NewsTranslation,
            (NewsTranslation.news_id == News.id) & (NewsTranslation.language == language),
        )
        .where(News.id.in_(news_ids))
    )

    return {str(news_id): title for news_id, title in await session.execute(query)}


async def missing_languages(session: AsyncSession, news_id: uuid.UUID) -> list[str]:
    query = select(NewsTranslation.language).where(NewsTranslation.news_id == news_id)

    done = set(await session.scalars(query))

    return [code for code in OTHER_LANGUAGES if code not in done]


async def untranslated(session: AsyncSession) -> list[uuid.UUID]:
    """Up to NEWS_RESEND_BATCH posts that lack a translation into some language, newest first."""
    query = (
        select(News.id)
        .outerjoin(NewsTranslation)
        .group_by(News.id)
        .having(func.count(NewsTranslation.language) < len(OTHER_LANGUAGES))
        .order_by(News.created_at.desc())
        .limit(NEWS_RESEND_BATCH)
    )

    return list(await session.scalars(query))


async def save_translations(
    session: AsyncSession,
    news_id: uuid.UUID,
    title: str,
    text: str,
    translations: dict[str, NewsTranslationIn],
) -> None:
    """Saves translations of the post as it reads `title` and `text`; nothing when it changed
    since or is gone. A translation saved again replaces the earlier one. The post's row is
    locked, so an edit can't happen between the check and the save."""
    row = await session.get(News, news_id, with_for_update=True)

    if row is None or (row.title, row.text) != (title, text):
        return

    for language, translation in translations.items():
        if language == DEFAULT_LANGUAGE:
            continue

        values = {"title": translation.title, "text": translation.text}
        await session.execute(
            insert(NewsTranslation)
            .values(news_id=news_id, language=language, **values)
            .on_conflict_do_update(
                index_elements=[NewsTranslation.news_id, NewsTranslation.language],
                set_=values,
            )
        )
