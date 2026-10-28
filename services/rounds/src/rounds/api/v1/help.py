from fastapi import APIRouter, Request, status
from fastapi.responses import RedirectResponse
from prepza_common.auth.human_check import require_human
from prepza_common.http.client_ip import limit_address
from prepza_common.i18n.i18n import request_language

from rounds.config import settings
from rounds.constants.help import HELP_CHAT_PATH
from rounds.schemas.contact import ContactRequest
from rounds.services import contact as contact_service

router = APIRouter(prefix="/help", tags=["help"])


@router.post("/chat", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
def help_chat() -> RedirectResponse:
    """The help chat moved to the assistant (POST /api/assistant/help/chat): the browser asks
    there again with the same request. Kept for one release, for pages loaded before it."""
    return RedirectResponse(HELP_CHAT_PATH, status.HTTP_307_TEMPORARY_REDIRECT)


@router.post("/contact", status_code=status.HTTP_204_NO_CONTENT)
async def contact(body: ContactRequest, request: Request) -> None:
    """The contact page's message; notifications emails it to prepza's inbox. Public, so the
    sender shows they're a person."""
    await require_human(request, settings.turnstile_secret_key)
    await contact_service.send(body, limit_address(request), request_language(request))
