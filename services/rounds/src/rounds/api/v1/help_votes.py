from uuid import UUID

from fastapi import APIRouter, status
from fastapi.responses import RedirectResponse

from rounds.constants.help import HELP_VOTE_PATH

router = APIRouter(prefix="/help", tags=["help"])


@router.put("/answers/{answer_id}/vote", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
def vote(answer_id: UUID) -> RedirectResponse:
    """The help chat's votes moved to the assistant (PUT /api/assistant/help/answers/{id}/vote):
    the browser sends the vote there again. Kept for one release, for pages loaded before it."""
    return RedirectResponse(
        HELP_VOTE_PATH.format(answer_id=answer_id), status.HTTP_307_TEMPORARY_REDIRECT
    )
