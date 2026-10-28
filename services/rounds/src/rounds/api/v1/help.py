from fastapi import APIRouter, status
from fastapi.responses import RedirectResponse

from rounds.constants.help import HELP_CHAT_PATH

router = APIRouter(prefix="/help", tags=["help"])


@router.post("/chat", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
def help_chat() -> RedirectResponse:
    """The help chat moved to the assistant (POST /api/assistant/help/chat): the browser asks
    there again with the same request. Kept for one release, for pages loaded before it."""
    return RedirectResponse(HELP_CHAT_PATH, status.HTTP_307_TEMPORARY_REDIRECT)
