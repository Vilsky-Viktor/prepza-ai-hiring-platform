"""Library's old internal news routes: news posts' titles for the bell (notifications) and their
text and translations (generation) now live in the site service, which the callers call. Kept one
release (microservices.md, 3) for a caller still running the version before, each answering what
site answers."""

from fastapi import APIRouter, Request, Response

from library.api.dependencies import ServiceCaller
from library.integrations.site_routes import forward

router = APIRouter(prefix="/internal/news", tags=["internal"])


@router.post("/titles")
async def news_titles(request: Request, caller: ServiceCaller) -> Response:
    return await forward(request)


@router.get("/{news_id}")
async def get_news_source(news_id: str, request: Request, caller: ServiceCaller) -> Response:
    return await forward(request)


@router.put("/{news_id}/translations")
async def save_news_translations(news_id: str, request: Request, caller: ServiceCaller) -> Response:
    return await forward(request)
