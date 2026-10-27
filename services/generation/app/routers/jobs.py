from fastapi import APIRouter, Request, status
from prepza_common.auth.google import Invoker

from app.schemas.campaigns import TranslateCampaign
from app.schemas.jobs import RunGeneration, VerifyQuestion
from app.schemas.news import TranslateNews
from app.services.jobs import run_generation
from app.services.translation_jobs import translate_campaign, translate_news
from app.services.verify import verify

router = APIRouter(prefix="/internal/jobs", tags=["jobs"], dependencies=[Invoker])


@router.post("/run-generation", status_code=status.HTTP_204_NO_CONTENT)
async def run_generation_job(body: RunGeneration, request: Request) -> None:
    """One Cloud Task: the whole generation, or up to its topic review."""
    await run_generation(request.app.state.graph, body.generation_id, body.resume)


@router.post("/verify-question", status_code=status.HTTP_204_NO_CONTENT)
async def verify_question_job(body: VerifyQuestion) -> None:
    await verify(body.question_id, body.flag, body.now)


@router.post("/translate-news", status_code=status.HTTP_204_NO_CONTENT)
async def translate_news_job(body: TranslateNews) -> None:
    """A failure answers with an error, so Cloud Tasks tries the missing languages again."""
    await translate_news(body.news_id)


@router.post("/translate-campaign", status_code=status.HTTP_204_NO_CONTENT)
async def translate_campaign_job(body: TranslateCampaign) -> None:
    """A failure answers with an error, so Cloud Tasks tries the missing languages again."""
    await translate_campaign(body.campaign_id)
