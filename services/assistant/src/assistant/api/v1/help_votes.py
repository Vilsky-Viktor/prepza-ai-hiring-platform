from uuid import UUID

from fastapi import APIRouter, Request, status
from prepza_common.http.client_ip import limit_address

from assistant.schemas.help_chat import HelpVoteIn
from assistant.services import help_votes

router = APIRouter(prefix="/help", tags=["help"])


@router.put("/answers/{answer_id}/vote", status_code=status.HTTP_204_NO_CONTENT)
async def vote(answer_id: UUID, body: HelpVoteIn, request: Request) -> None:
    """A thumbs up or down on one of the help chat's answers, for visitors too: one an answer, a
    new vote replaces it, null clears it. The help chat keeps no conversation, so the answer's
    signature (from its last event) shows the vote comes from the page that got it. Sent on to
    Langfuse as a score on the answer's trace when that's set up."""
    await help_votes.vote(answer_id, body, limit_address(request))
