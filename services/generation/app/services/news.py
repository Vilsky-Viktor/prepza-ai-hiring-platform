from uuid import UUID

from prepza_common.constants import MAX_NEWS_TEXT_LENGTH, MAX_NEWS_TITLE_LENGTH

from app.constants.actions import NEWS_TRANSLATION
from app.helpers.prompts import language_name
from app.integrations import library
from app.integrations.usage import ai_run
from app.prompts.news import NEWS_TRANSLATION_INPUT, NEWS_TRANSLATION_SYSTEM
from app.schemas.news import NewsSource, TranslatedNews
from app.services.translations import translate_fields, translate_missing

LIMITS = {"title": MAX_NEWS_TITLE_LENGTH, "text": MAX_NEWS_TEXT_LENGTH}


async def translate_one(source: NewsSource, language: str) -> TranslatedNews:
    """The post in `language`; raises when the model fails or writes past the post's limits."""
    request = NEWS_TRANSLATION_INPUT.format(
        language=language_name(language), title=source.title, text=source.text
    )

    return await translate_fields(
        TranslatedNews, NEWS_TRANSLATION_SYSTEM, request, LIMITS, language
    )


async def translate_news(news_id: UUID) -> None:
    """Translates the post into each language it lacks and saves those that worked; raises when
    a language failed, so the job runs again. A translated language is skipped."""
    source = await library.get_news_source(news_id)

    if source is None or not source.missing:
        return

    async def save(done: dict[str, TranslatedNews]) -> None:
        await library.save_news_translations(news_id, source, done)

    async with ai_run(NEWS_TRANSLATION, subject_id=news_id):
        await translate_missing(
            f"news post {news_id}",
            source.missing,
            lambda language: translate_one(source, language),
            save,
        )
