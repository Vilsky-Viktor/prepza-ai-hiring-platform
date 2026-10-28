from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from prepza_common.auth.auth import OptionalUser
from prepza_common.http.sse import event_stream
from prepza_common.http.visitor_country import VisitorCountry
from prepza_common.i18n.i18n import request_language

from assistant.schemas.help_chat import HelpChatRequest
from assistant.services import help_answers

router = APIRouter(prefix="/help", tags=["help"])


@router.post("/chat")
async def help_chat(
    body: HelpChatRequest, request: Request, user: OptionalUser, country: VisitorCountry = None
) -> StreamingResponse:
    """Answers questions about prepza, for visitors too, from the site's documents (site's).
    Streams server-sent events: {"delta"}... (and a {"block"} sign-in card when a visitor asks
    to sign in or sign up), then {"done"} or {"error"}. Prices are in the visitor's country's
    currency (US dollars without one). Refused during the emergency pause, as it's AI. A
    conversation with a secret in it (a key, a token, a password) is answered at once, before
    anything else, with a fixed reply ({"removed"} first: the panel drops that message), and
    nothing of it is used."""
    language = request_language(request)

    return event_stream(await help_answers.start(body, request, user, country, language))
