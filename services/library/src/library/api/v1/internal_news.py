from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from library.api.dependencies import ServiceCaller
from library.repositories import news
from library.schemas.news import NewsSourceOut, NewsTitlesIn, NewsTitlesOut, NewsTranslationsIn

# News posts' translations, written by generation (its translate-news job), and their titles
# for the bell (notifications).
router = APIRouter(prefix="/internal/news", tags=["internal"])


@router.post("/titles")
async def news_titles(body: NewsTitlesIn, caller: ServiceCaller) -> NewsTitlesOut:
    """The posts' titles in the reader's language, in English until it's translated."""
    return NewsTitlesOut(titles=await news.titles(body.news_ids, body.language))


@router.get("/{news_id}")
async def get_news_source(news_id: UUID, caller: ServiceCaller) -> NewsSourceOut:
    post = await news.get(news_id)

    if post is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")

    return NewsSourceOut(
        title=post.title, text=post.text, missing=await news.missing_languages(news_id)
    )


@router.put("/{news_id}/translations", status_code=status.HTTP_204_NO_CONTENT)
async def save_news_translations(
    news_id: UUID, body: NewsTranslationsIn, caller: ServiceCaller
) -> None:
    """Safe to repeat; translations of an older version of the post, or of a deleted one, are
    dropped."""
    await news.save_translations(news_id, body.title, body.text, body.translations)
