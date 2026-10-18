from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from prepza_common.answer_votes import mirror_vote
from prepza_common.tokens import same_secret

from app.config.settings import settings
from app.constants.help import NO_SUCH_ANSWER
from app.helpers.help_replies import vote_signature
from app.schemas.help import HelpVoteIn
from app.storage import help_votes

router = APIRouter(prefix="/help", tags=["help"])


@router.put("/answers/{answer_id}/vote", status_code=status.HTTP_204_NO_CONTENT)
async def vote(answer_id: UUID, body: HelpVoteIn) -> None:
    """A thumbs up or down on one of the help chat's answers, for visitors too: one an answer, a
    new vote replaces it, null clears it. The help chat keeps no conversation, so the answer's
    signature (from its last event) shows the vote comes from the page that got it. Sent on to
    Langfuse as a score on the answer's trace when that's set up."""
    expected = vote_signature(answer_id, body.trace_id, settings.service_secret)

    if not same_secret(body.signature, expected):
        raise HTTPException(status.HTTP_404_NOT_FOUND, NO_SUCH_ANSWER)

    await help_votes.save(answer_id, body.trace_id, body.value)
    mirror_vote(body.trace_id, lambda: help_votes.vote_of(answer_id))
