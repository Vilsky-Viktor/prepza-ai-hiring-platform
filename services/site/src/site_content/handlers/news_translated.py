from testee_common.events.news import NewsTranslated

from site_content.services import news


async def handle(data: dict) -> None:
    """Generation translated a news post: saved while the post still reads as the English
    translated, so a late translation of an older text is dropped, and a redelivery replaces
    the same translation with itself."""
    await news.save_translations(NewsTranslated.model_validate(data))
