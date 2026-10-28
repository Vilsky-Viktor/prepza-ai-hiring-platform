from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from library.api.dependencies import ServiceCaller
from library.core.db import Session
from library.repositories import news
from library.schemas.news import NewsSourceOut, NewsTitlesIn, NewsTitlesOut, NewsTranslationsIn
from library.services import news as news_service

# News posts' translations, written by generation (its translate-news job), and their titles
# for the bell (notifications).
router = APIRouter(prefix="/internal/news", tags=["internal"])


@router.post("/titles")
async def news_titles(body: NewsTitlesIn, caller: ServiceCaller) -> NewsTitlesOut:
    """The posts' titles in the reader's language, in English until it's translated."""
    async with Session() as session:
        return NewsTitlesOut(titles=await news.titles(session, body.news_ids, body.language))


@router.get("/{news_id}")
async def get_news_source(news_id: UUID, caller: ServiceCaller) -> NewsSourceOut:
    found = await news_service.source(news_id)

    if found is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")

    post, missing = found

    return NewsSourceOut(title=post.title, text=post.text, missing=missing)


@router.put("/{news_id}/translations", status_code=status.HTTP_204_NO_CONTENT)
async def save_news_translations(
    news_id: UUID, body: NewsTranslationsIn, caller: ServiceCaller
) -> None:
    """Safe to repeat; translations of an older version of the post, or of a deleted one, are
    dropped."""
    await news_service.save_translations(news_id, body.title, body.text, body.translations)
