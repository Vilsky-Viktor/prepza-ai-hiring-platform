from prepza_common.config.constants import MAX_NEWS_TEXT_LENGTH, MAX_NEWS_TITLE_LENGTH

from app.helpers.prompts import language_name
from app.prompts.news import NEWS_TRANSLATION_INPUT
from app.schemas.news import NewsSource

LIMITS = {"title": MAX_NEWS_TITLE_LENGTH, "text": MAX_NEWS_TEXT_LENGTH}


def news_request(source: NewsSource, language: str) -> str:
    """The user's message of a post's translation: the post, tagged, and the language."""
    return NEWS_TRANSLATION_INPUT.format(
        language=language_name(language), title=source.title, text=source.text
    )
