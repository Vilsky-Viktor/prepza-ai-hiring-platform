from uuid import UUID

import httpx
from prepza_common.ai.sets import AddedQuestionsIn, AdditionContext, PreparationIn, QuestionIn
from prepza_common.http import http
from prepza_common.http.http import bearer

from generation.config import settings
from generation.core.security import service_token
from generation.schemas.library import ReuseIn
from generation.schemas.news import NewsSource, TranslatedNews
from generation.schemas.patterns import QualitySignal
from generation.schemas.regenerate import QuestionContext, RegeneratedQuestion
from generation.schemas.verify import QuestionQuality


async def create_interview(preparation: PreparationIn) -> UUID:
    return await _create("interviews", preparation)


async def create_template(preparation: PreparationIn) -> UUID:
    return await _create("templates", preparation)


async def _create(kind: str, preparation: PreparationIn) -> UUID:
    response = await http.get_client().post(
        f"{settings.library_url}/internal/{kind}",
        json=preparation.model_dump(mode="json"),
        headers=bearer(service_token("library")),
    )

    response.raise_for_status()

    return UUID(response.json()["id"])


async def get_addition_context(template_id: UUID) -> AdditionContext | None:
    """A template's topics with their questions' texts and what each pool lacks; None when
    there's no such template."""
    response = await http.get_client().get(
        f"{settings.library_url}/internal/templates/{template_id}/additions",
        headers=bearer(service_token("library")),
    )

    if response.status_code == httpx.codes.NOT_FOUND:
        return None

    response.raise_for_status()

    return AdditionContext.model_validate(response.json())


async def add_questions(template_id: UUID, added: AddedQuestionsIn) -> list[list[UUID]]:
    """Saves new questions in a template's topics, all at once; each topic's new ids."""
    response = await http.get_client().post(
        f"{settings.library_url}/internal/templates/{template_id}/questions",
        json=added.model_dump(mode="json"),
        headers=bearer(service_token("library")),
    )

    response.raise_for_status()

    return [[UUID(question_id) for question_id in topic] for topic in response.json()]


async def delete_set(set_id: UUID) -> None:
    """Deletes a saved test or template; safe to repeat."""
    response = await http.get_client().delete(
        f"{settings.library_url}/internal/interviews/{set_id}",
        headers=bearer(service_token("library")),
    )

    response.raise_for_status()


async def get_question_context(question_id: UUID) -> QuestionContext | None:
    response = await http.get_client().get(
        f"{settings.library_url}/internal/questions/{question_id}/context",
        headers=bearer(service_token("library")),
    )

    if response.status_code == httpx.codes.NOT_FOUND:
        return None

    response.raise_for_status()

    return QuestionContext.model_validate(response.json())


async def replace_question(question_id: UUID, question: RegeneratedQuestion) -> None:
    response = await http.get_client().put(
        f"{settings.library_url}/internal/questions/{question_id}",
        json=question.model_dump(),
        headers=bearer(service_token("library")),
    )

    response.raise_for_status()


async def get_question_quality(question_id: UUID) -> QuestionQuality | None:
    response = await http.get_client().get(
        f"{settings.library_url}/internal/questions/{question_id}/quality",
        headers=bearer(service_token("library")),
    )

    if response.status_code == httpx.codes.NOT_FOUND:
        return None

    response.raise_for_status()

    return QuestionQuality.model_validate(response.json())


async def keep_question(question_id: UUID) -> None:
    response = await http.get_client().post(
        f"{settings.library_url}/internal/questions/{question_id}/keep",
        headers=bearer(service_token("library")),
    )

    response.raise_for_status()


async def find_reusable(request: ReuseIn) -> list[QuestionIn]:
    """Proven questions from other tests on a similar topic."""
    response = await http.get_client().post(
        f"{settings.library_url}/internal/reuse",
        json=request.model_dump(),
        headers=bearer(service_token("library")),
    )

    response.raise_for_status()

    return [QuestionIn.model_validate(item) for item in response.json()]


async def missing_embeddings(limit: int) -> list[dict]:
    """Template topics without an embedding: [{"id", "title", "subtopics"}]."""
    response = await http.get_client().get(
        f"{settings.library_url}/internal/embeddings/missing",
        params={"limit": limit},
        headers=bearer(service_token("library")),
    )

    response.raise_for_status()

    return response.json()


async def save_embeddings(embeddings: dict[str, list[float]]) -> None:
    response = await http.get_client().put(
        f"{settings.library_url}/internal/embeddings",
        json=[{"id": topic_id, "embedding": value} for topic_id, value in embeddings.items()],
        headers=bearer(service_token("library")),
    )

    response.raise_for_status()


async def untagged_code(limit: int, text: bool = False, after: str | None = None) -> list[dict]:
    """Questions whose example has no language yet, or with `text` the ones tagged "text", in id
    order after `after`: [{"id", "text"}]."""
    params = {"limit": limit, "text": text} | ({"after": after} if after else {})
    response = await http.get_client().get(
        f"{settings.library_url}/internal/code/untagged",
        params=params,
        headers=bearer(service_token("library")),
    )

    response.raise_for_status()

    return response.json()


async def save_code_languages(languages: dict[str, str], text: bool = False) -> None:
    response = await http.get_client().put(
        f"{settings.library_url}/internal/code/languages",
        params={"text": text},
        json=[{"id": question_id, "language": value} for question_id, value in languages.items()],
        headers=bearer(service_token("library")),
    )

    response.raise_for_status()


async def get_question_ids(set_id: UUID) -> list[list[UUID]]:
    """Each topic's question ids in a set."""
    response = await http.get_client().get(
        f"{settings.library_url}/internal/sets/{set_id}/content",
        headers=bearer(service_token("library")),
    )

    response.raise_for_status()

    return [
        [UUID(question["id"]) for question in topic["questions"]]
        for topic in response.json()["topics"]
    ]


async def get_news_source(news_id: UUID) -> NewsSource | None:
    """A news post's English text and the languages it lacks; None once it's deleted."""
    response = await http.get_client().get(
        f"{settings.library_url}/internal/news/{news_id}",
        headers=bearer(service_token("library")),
    )

    if response.status_code == httpx.codes.NOT_FOUND:
        return None

    response.raise_for_status()

    return NewsSource.model_validate(response.json())


async def save_news_translations(
    news_id: UUID, source: NewsSource, translations: dict[str, TranslatedNews]
) -> None:
    """Saves the translations of `source`; the library drops them if the post changed since."""
    response = await http.get_client().put(
        f"{settings.library_url}/internal/news/{news_id}/translations",
        json={
            "title": source.title,
            "text": source.text,
            "translations": {code: item.model_dump() for code, item in translations.items()},
        },
        headers=bearer(service_token("library")),
    )

    response.raise_for_status()


async def quality_signals(days: int) -> list[QualitySignal]:
    """Questions flagged or replaced in the last `days`, across every company and template,
    without ids; library gives them to this service only."""
    response = await http.get_client().get(
        f"{settings.library_url}/internal/questions/signals",
        params={"days": days},
        headers=bearer(service_token("library")),
    )

    response.raise_for_status()

    return [QualitySignal.model_validate(item) for item in response.json()]
