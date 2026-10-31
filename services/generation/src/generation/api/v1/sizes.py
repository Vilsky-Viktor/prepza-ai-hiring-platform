from fastapi import APIRouter
from testee_common.limits.limits import limit

from generation.helpers.questions import topic_size_name
from generation.integrations.redis import get_redis
from generation.schemas.sizes import SizesOut

router = APIRouter(tags=["sizes"])


@router.get("/sizes")
async def sizes() -> SizesOut:
    """How big a new interview is made, for the home page's facts: public, the current Controls
    values."""
    return SizesOut(questions_per_topic=await limit(get_redis(), topic_size_name(False)))
