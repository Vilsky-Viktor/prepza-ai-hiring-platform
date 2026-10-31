from fastapi import APIRouter
from testee_common.config.constants import LANGUAGES

router = APIRouter(tags=["languages"])


@router.get("/languages")
async def list_languages() -> list[str]:
    """The languages tests can be generated in, for the "generate in" choice."""
    return list(LANGUAGES)
