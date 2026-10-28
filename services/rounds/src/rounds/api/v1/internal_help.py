from fastapi import APIRouter, Query

from rounds.api.dependencies import ServiceCaller
from rounds.constants.help import MAX_PAGE_KEY_LENGTH
from rounds.schemas.help import HelpKnowledgeOut
from rounds.services.help import chat_knowledge

router = APIRouter(prefix="/internal/help", tags=["internal"])


@router.get("/knowledge")
async def knowledge(
    caller: ServiceCaller,
    country: str | None = None,
    page: str | None = Query(default=None, max_length=MAX_PAGE_KEY_LENGTH),
) -> HelpKnowledgeOut:
    """What the assistant's help chat answers from, in English: the platform guide with the
    prices in the currency of the visitor's `country` (as the load balancer names it; billing
    checks it, and an unknown one means US dollars), and the guide of the `page` asked on
    (its key; an unknown one has none)."""
    return await chat_knowledge(country, page)
