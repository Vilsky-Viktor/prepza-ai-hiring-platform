import logging
import uuid

from app.integrations import generation
from app.storage import news

logger = logging.getLogger(__name__)


async def send_to_translator(news_id: uuid.UUID) -> None:
    """Never raises: the post is saved first, and resend_untranslated sends it again later."""
    try:
        await generation.translate_news(news_id)
    except Exception:
        logger.exception("Couldn't send news post %s to be translated", news_id)


async def resend_untranslated() -> int:
    """Sends the posts that still lack a translation to be translated again, a batch a run (the
    newest first); how many."""
    ids = await news.untranslated()

    for news_id in ids:
        await send_to_translator(news_id)

    return len(ids)
