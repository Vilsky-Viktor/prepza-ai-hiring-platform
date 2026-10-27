from uuid import UUID

from prepza_common.http import http
from prepza_common.http.http import bearer

from app.config.settings import settings
from app.service_auth import service_token


async def verify_question(question_id: UUID, flag: str, now: bool = False) -> None:
    """Queues the verifier for a newly flagged question; raises if generation can't."""
    response = await http.get_client().post(
        f"{settings.generation_url}/internal/questions/{question_id}/verify",
        json={"flag": flag, "now": now},
        headers=bearer(service_token("generation")),
    )

    response.raise_for_status()


async def translate_news(news_id: UUID) -> None:
    """Queues the post's translation into every language it lacks; raises if generation can't."""
    response = await http.get_client().post(
        f"{settings.generation_url}/internal/news/{news_id}/translate",
        headers=bearer(service_token("generation")),
    )

    response.raise_for_status()
