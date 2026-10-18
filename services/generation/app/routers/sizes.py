from fastapi import APIRouter
from prepza_common.limits import limit

from app.helpers.questions import topic_size_name
from app.integrations.redis import get_redis
from app.schemas.sizes import SizesOut

router = APIRouter(tags=["sizes"])


@router.get("/sizes")
async def sizes() -> SizesOut:
    """How big a new interview is made, for the home page's facts: public, the current Controls
    values."""
    return SizesOut(questions_per_topic=await limit(get_redis(), topic_size_name(False)))
