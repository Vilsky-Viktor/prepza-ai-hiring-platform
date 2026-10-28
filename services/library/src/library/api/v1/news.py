from fastapi import APIRouter, Request
from prepza_common.db.paging import PageParams
from prepza_common.i18n.i18n import request_language

from library.core.db import Session
from library.repositories import news
from library.schemas.news import NewsOut

# The news page: public, newest first, in the reader's language (Accept-Language) where the post
# is translated, in English where it isn't yet.
router = APIRouter(prefix="/news", tags=["news"])


@router.get("")
async def list_news(page: PageParams, request: Request) -> list[NewsOut]:
    async with Session() as session:
        rows = await news.list_news(session, request_language(request), page.offset, page.limit)

    return [
        NewsOut(
            id=post.id,
            title=title,
            text=text,
            published_on=post.published_on,
            updated_at=post.updated_at,
        )
        for post, title, text in rows
    ]
