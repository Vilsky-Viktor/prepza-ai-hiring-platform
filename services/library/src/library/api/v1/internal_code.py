import uuid

from fastapi import APIRouter, Query, status

from library.api.dependencies import ServiceCaller
from library.constants.code import MAX_UNTAGGED_BATCH, TEXT_FENCE, UNTAGGED_FENCE
from library.core.db import Session
from library.repositories import code
from library.schemas.code import CodeLanguageIn, UntaggedQuestion
from library.services import code as code_service

router = APIRouter(prefix="/internal", tags=["internal"])


@router.get("/code/untagged")
async def list_untagged_code(
    caller: ServiceCaller,
    limit: int = Query(MAX_UNTAGGED_BATCH, ge=1, le=MAX_UNTAGGED_BATCH),
    text: bool = False,
    after: uuid.UUID | None = None,
) -> list[UntaggedQuestion]:
    """Questions whose example has no language yet, or with `text` the ones tagged "text", in id
    order after `after`: for generation's tag_code_languages job."""
    async with Session() as session:
        found = await code.untagged(session, limit, TEXT_FENCE if text else UNTAGGED_FENCE, after)

    return [UntaggedQuestion(id=question_id, text=body) for question_id, body in found]


@router.put("/code/languages", status_code=status.HTTP_204_NO_CONTENT)
async def save_code_languages(
    body: list[CodeLanguageIn], caller: ServiceCaller, text: bool = False
) -> None:
    """Each listed question's example gets its language; with `text`, ones tagged "text"."""
    await code_service.tag(
        {item.id: item.language for item in body}, TEXT_FENCE if text else UNTAGGED_FENCE
    )
