import logging
import uuid

from prepza_common.events.news import NewsTranslated

from site_content.core.db import Session
from site_content.helpers.notifications import news_notification
from site_content.integrations import generation
from site_content.models.news import News
from site_content.repositories import news, outbox
from site_content.schemas.news import NewsIn
from site_content.services import outbox as outbox_service

logger = logging.getLogger(__name__)


async def send_to_translator(news_id: uuid.UUID) -> None:
    """Sends the post's English title and text and the languages it lacks to generation; nothing
    once it's deleted. Never raises: the post is saved first, and resend_untranslated sends it
    again later."""
    try:
        found = await source(news_id)

        if found is None:
            return

        post, missing = found
        body = {"title": post.title, "text": post.text, "missing": missing}
        await generation.translate_news(news_id, body)
    except Exception:
        logger.exception("Couldn't send news post %s to be translated", news_id)


async def resend_untranslated() -> int:
    """Sends the posts that still lack a translation to be translated again, a batch a run (the
    newest first); how many."""
    async with Session() as session:
        ids = await news.untranslated(session)

    for news_id in ids:
        await send_to_translator(news_id)

    return len(ids)


async def create(post: NewsIn) -> News:
    """Saves the post with its notification for everyone, in one save, then sends it to be
    translated."""
    async with Session.begin() as session:
        row = await news.create(session, post)
        outbox.notify(session, news_notification(row))

    await outbox_service.flush_quietly()
    await send_to_translator(row.id)

    return row


async def update(news_id: uuid.UUID, post: NewsIn) -> tuple[News, int] | None:
    """Saves the post, and how many languages it's translated into. A changed title or text
    deletes its translations (the page shows the English post until it's translated again) and
    is translated again; a new date alone keeps them. None when it's gone."""
    async with Session.begin() as session:
        row = await news.lock(session, news_id)

        if row is None:
            return None

        changed = (row.title, row.text) != (post.title, post.text)

        if changed:
            await news.clear_translations(session, news_id)

        row = await news.save(session, row, post)
        missing = await news.missing_languages(session, news_id)

    if changed:
        await send_to_translator(row.id)

    return row, len(news.OTHER_LANGUAGES) - len(missing)


async def remove(news_id: uuid.UUID) -> None:
    """Deletes the post with its translations, and its notification goes too; safe to repeat."""
    async with Session.begin() as session:
        await news.remove(session, news_id)

    await outbox_service.flush_quietly()


async def save_translations(event: NewsTranslated) -> None:
    """Generation's translations of the post as it read `event.title` and `event.text`; dropped
    when it changed since or is gone, and saved again they replace themselves."""
    async with Session.begin() as session:
        await news.save_translations(
            session, event.news_id, event.title, event.text, event.translations
        )


async def source(news_id: uuid.UUID) -> tuple[News, list[str]] | None:
    """The post in English and the languages it still lacks; None when it's gone."""
    async with Session() as session:
        post = await news.get(session, news_id)

        if post is None:
            return None

        return post, await news.missing_languages(session, news_id)
