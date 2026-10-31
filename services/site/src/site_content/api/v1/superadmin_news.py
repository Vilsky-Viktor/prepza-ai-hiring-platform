from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from testee_common.auth.superadmin import SuperadminUser
from testee_common.db.paging import PageParams

from site_content.core.db import Session
from site_content.models.news import News
from site_content.repositories import news
from site_content.schemas.news import AdminNewsOut, NewsIn
from site_content.services import news as news_service

# The admin zone's news tab: a superadmin writes posts in English; each is translated into the
# other languages after it's saved. Everyone else gets "not found".
router = APIRouter(prefix="/superadmin/news", tags=["superadmin"])


def admin_post(post: News, translations: int) -> AdminNewsOut:
    return AdminNewsOut(
        id=post.id,
        title=post.title,
        text=post.text,
        published_on=post.published_on,
        updated_at=post.updated_at,
        translated=translations >= len(news.OTHER_LANGUAGES),
    )


@router.get("")
async def list_news(superadmin: SuperadminUser, page: PageParams) -> list[AdminNewsOut]:
    async with Session() as session:
        rows = await news.list_with_counts(session, page.offset, page.limit)

    return [admin_post(post, count) for post, count in rows]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_news(body: NewsIn, superadmin: SuperadminUser) -> AdminNewsOut:
    return admin_post(await news_service.create(body), 0)


@router.put("/{news_id}")
async def update_news(news_id: UUID, body: NewsIn, superadmin: SuperadminUser) -> AdminNewsOut:
    """A changed title or text is translated again; a new date alone keeps the translations."""
    saved = await news_service.update(news_id, body)

    if saved is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")

    return admin_post(*saved)


@router.delete("/{news_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_news(news_id: UUID, superadmin: SuperadminUser) -> None:
    await news_service.remove(news_id)
