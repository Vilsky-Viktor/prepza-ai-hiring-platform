from fastapi import APIRouter, Query, status

from library.api.dependencies import ServiceCaller
from library.constants.reuse import MAX_EMBEDDING_BATCH
from library.core.db import Session
from library.repositories import reuse
from library.schemas.reuse import ReusedQuestion, ReuseIn, TopicEmbedding, TopicToEmbed
from library.services import reuse as reuse_service

router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("/reuse")
async def find_reusable(body: ReuseIn, caller: ServiceCaller) -> list[ReusedQuestion]:
    """Proven questions on a similar topic, for a new generation: templates' company questions
    and, for a company's interview, the shared bank's."""
    async with Session() as session:
        found = await reuse.find(
            session, body.embedding, body.level, body.language, body.count, body.company_id
        )

    return [
        ReusedQuestion(source_id=source_id, text=text, options=options)
        for source_id, text, options in found
    ]


@router.get("/embeddings/missing")
async def list_missing_embeddings(
    caller: ServiceCaller, limit: int = Query(MAX_EMBEDDING_BATCH, ge=1, le=MAX_EMBEDDING_BATCH)
) -> list[TopicToEmbed]:
    """Template topics without an embedding, for generation's embed_templates job."""
    async with Session() as session:
        found = await reuse.missing(session, limit)

    return [
        TopicToEmbed(id=topic_id, title=title, subtopics=subtopics)
        for topic_id, title, subtopics in found
    ]


@router.put("/embeddings", status_code=status.HTTP_204_NO_CONTENT)
async def save_embeddings(body: list[TopicEmbedding], caller: ServiceCaller) -> None:
    await reuse_service.save_embeddings({item.id: item.embedding for item in body})
