from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from prepza_common.auth.superadmin import SuperadminUser
from prepza_common.db.paging import PageParams

from app.models.news import News
from app.schemas.news import AdminNewsOut, NewsIn
from app.services import outbox as outbox_service
from app.services.news import send_to_translator
from app.storage import news

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
    rows = await news.list_with_counts(page.offset, page.limit)

    return [admin_post(post, count) for post, count in rows]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_news(body: NewsIn, superadmin: SuperadminUser) -> AdminNewsOut:
    post = await news.create(body)
    await outbox_service.flush_quietly()
    await send_to_translator(post.id)

    return admin_post(post, 0)


@router.put("/{news_id}")
async def update_news(news_id: UUID, body: NewsIn, superadmin: SuperadminUser) -> AdminNewsOut:
    """A changed title or text is translated again; a new date alone keeps the translations."""
    saved = await news.update(news_id, body)

    if saved is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")

    post, changed = saved

    if changed:
        await send_to_translator(post.id)

    missing = await news.missing_languages(post.id)

    return admin_post(post, len(news.OTHER_LANGUAGES) - len(missing))


@router.delete("/{news_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_news(news_id: UUID, superadmin: SuperadminUser) -> None:
    await news.remove(news_id)
    await outbox_service.flush_quietly()
