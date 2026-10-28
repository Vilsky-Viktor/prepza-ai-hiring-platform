import logging
import uuid

import anyio
from fastapi import APIRouter, HTTPException, Path, Query, Request, status
from fastapi.responses import PlainTextResponse, StreamingResponse
from prepza_common.ai import ai_cap
from prepza_common.ai.ai_constants import Outcome
from prepza_common.ai.ai_usage import provider_refused
from prepza_common.ai.secrets_check import secret_in
from prepza_common.ai.tracing import new_trace_id
from prepza_common.auth.auth import OptionalUser
from prepza_common.auth.human_check import require_human
from prepza_common.auth.user import Language
from prepza_common.config.constants import DEFAULT_LANGUAGE, LEGAL_VERSIONS
from prepza_common.events.analytics import track
from prepza_common.http.client_ip import limit_address
from prepza_common.http.sse import event_stream, sse_event
from prepza_common.http.visitor_country import VisitorCountry
from prepza_common.i18n.i18n import request_language, translate
from prepza_common.limits.pause import refuse_if_paused
from prepza_common.limits.rate_limit import hit, spend

from rounds.config import settings
from rounds.constants.help import (
    HELP_ALL_KEY,
    HELP_CHAT,
    HELP_SPEND_KEY,
    MAX_GUIDE_SLUG_LENGTH,
    MAX_PAGE_KEY_LENGTH,
    NO_SUCH_GUIDE,
    NO_SUCH_PAGE,
    PAGE_ARTICLES,
    PRICES_UNAVAILABLE,
    HelpRole,
    LegalDocument,
)
from rounds.constants.legal import NO_SUCH_VERSION
from rounds.constants.rounds import CHAT_FAILED
from rounds.helpers import legal
from rounds.helpers.guide_articles import guide_article, guide_articles
from rounds.helpers.help import faq_items
from rounds.helpers.help_replies import help_signing_key, reply_signature, trusted, vote_signature
from rounds.helpers.page_guides import page_guide
from rounds.helpers.sign_in import secret_reply, with_sign_in
from rounds.integrations import billing
from rounds.integrations.redis import get_redis
from rounds.schemas.contact import ContactRequest
from rounds.schemas.help import (
    FaqItemOut,
    GuideItemOut,
    GuideOut,
    HelpChatRequest,
    LegalOut,
    PageGuideOut,
)
from rounds.services import contact as contact_service
from rounds.services.help import build_messages, platform_guide, record_answer, stream_reply

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/help", tags=["help"])


@router.get("/faq")
async def get_faq(request: Request, country: str | None = None) -> list[FaqItemOut]:
    """The FAQ in the page's language, with today's prices in the currency of the visitor's
    `country` (the site passes it on; US dollars without one); public. Without prices (billing not
    answering) it's refused rather than built with blanks: the site keeps its last good page."""
    catalog = await billing.catalog(country)

    if catalog is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, PRICES_UNAVAILABLE)

    items = faq_items(request_language(request), catalog)

    return [FaqItemOut(**item) for item in items]


@router.get("/guide", response_class=PlainTextResponse)
async def get_guide(request: Request) -> str:
    """Everything prepza's help chat answers from, as text: how prepza works and how to use it,
    the FAQ in the page's language, today's prices, the terms and the privacy policy; public."""
    return await platform_guide(request_language(request))


@router.get("/pages/{key}")
async def get_page_guide(
    request: Request, key: str = Path(max_length=MAX_PAGE_KEY_LENGTH)
) -> PageGuideOut:
    """A page's guide, by its key, in the page's language (English until it's translated), with
    the guide article to read more in, if any: its info button shows it, and the assistant reads
    it about the page the user is on; public."""
    language = request_language(request)
    guide = page_guide(key, language)

    if guide is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NO_SUCH_PAGE)

    article = guide_article(PAGE_ARTICLES[key], language) if key in PAGE_ARTICLES else None

    return PageGuideOut(key=key, **guide, article=article)


@router.get("/guides")
def list_guides(request: Request) -> list[GuideItemOut]:
    """The site's guide articles (hiring advice and how-tos: hiring engineers, interviewing in
    the age of AI, AI hiring and the law, ATS integration, MCP and the API, ...), by title, in
    the page's language where translated; public."""
    return [GuideItemOut(**item) for item in guide_articles(request_language(request))]


@router.get("/guides/{slug}")
def get_guide_article(
    request: Request, slug: str = Path(max_length=MAX_GUIDE_SLUG_LENGTH)
) -> GuideOut:
    """One guide article, by its slug, with its Markdown text, in the page's language (English
    until it's translated); public."""
    article = guide_article(slug, request_language(request))

    if article is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NO_SUCH_GUIDE)

    return GuideOut(**article)


@router.get("/legal/{document}")
def get_legal(
    document: LegalDocument,
    version: str | None = Query(default=None, max_length=10),
    language: Language = DEFAULT_LANGUAGE,
) -> LegalOut:
    """The terms, the privacy policy or the DPA: the current version, or an earlier one, with
    every published version (the day each applies from), in `language` when it's translated
    (the English text is the binding one); public."""
    text = legal.version(document, version)

    if text is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NO_SUCH_VERSION)

    shown = version or LEGAL_VERSIONS[document]
    applies = legal.in_force(document)
    translated = legal.translation(document, shown, language)

    return LegalOut(
        **(translated or text),
        language=language if translated else DEFAULT_LANGUAGE,
        version=shown,
        state=legal.state(shown, applies),
        current=LEGAL_VERSIONS[document],
        in_force=applies,
        versions=legal.versions(document),
    )


@router.post("/chat")
async def help_chat(
    body: HelpChatRequest, request: Request, user: OptionalUser, country: VisitorCountry = None
) -> StreamingResponse:
    """Answers questions about prepza, for visitors too. Streams server-sent events:
    {"delta"}... (and a {"block"} sign-in card when a visitor asks to sign in or sign up), then
    {"done"} or {"error"}. Prices are in the visitor's country's currency (US dollars without
    one). Refused during the emergency pause, as it's AI. A conversation with a
    secret in it (a key, a token, a password) is answered at once, before anything else, with a
    fixed reply ({"removed"} first: the panel drops that message), and nothing of it is used."""
    language = request_language(request)

    if secret_in([message.content for message in body.messages]) is not None:
        return event_stream(secret_reply(language))

    redis = get_redis()
    user_id = user.uid if user else None
    await refuse_if_paused(redis, HELP_CHAT, user_id=user_id)
    conversation = trusted(body.messages, help_signing_key(settings.service_secret))

    # A visitor shows they're a person once, until the chat has a reply: the chat has no id to
    # remember it by, a signed reply came only after the check, and it shows nothing to most.
    if user is None and not any(item.role == HelpRole.ASSISTANT for item in conversation):
        await require_human(request, settings.turnstile_secret_key)

    if user:
        await hit(redis, f"rate:help:{user.uid}", "HELP_USER_LIMIT", user_id=user_id)

    await hit(redis, f"rate:help:ip:{limit_address(request)}", "HELP_IP_LIMIT")
    await hit(redis, HELP_ALL_KEY, "HELP_DAILY_LIMIT", user_id=user_id)
    # The day's token budget, checked before the answer and counted after it.
    await spend(redis, HELP_SPEND_KEY, 0, "HELP_TOKENS_PER_DAY", user_id=user_id)
    # The help chat is never a paid company's, so the unpaid AI spend cap always applies.
    await ai_cap.refuse_if_capped(redis, user_id=user_id)

    catalog = await billing.catalog(country)
    messages = await build_messages(conversation, language, catalog, body.page)
    used: dict = {}
    # The answer's id, which a vote on it names, and its Langfuse trace when that's set up.
    answer_id = uuid.uuid4()
    trace_id = new_trace_id()

    async def events():
        reply = ""
        # Until the answer is written whole, a visitor leaving cut it short.
        outcome = Outcome.CUT

        try:
            async for event in with_sign_in(
                stream_reply(messages, used, trace_id, str(body.chat_id) if body.chat_id else None)
            ):
                reply += event.get("delta", "")
                yield sse_event(event)

            outcome = Outcome.OK
        except Exception as error:
            outcome = Outcome.FAILED
            logger.exception("Help chat failed")
            await provider_refused(error, HELP_CHAT, user_id=user_id)
            yield sse_event({"error": translate(CHAT_FAILED, language)})

            return
        finally:
            # However the answer ends, its call is recorded and its tokens count. Shielded, as a
            # visitor leaving cancels the request.
            with anyio.CancelScope(shield=True):
                await record_answer(redis, messages, reply, used.get("usage"), outcome, user_id)

        await track("help_chat_turn", user_id=user_id, turn=len(body.messages))

        # The page sends the signature back with the reply, which the next answer then reads,
        # and the answer's id, trace and vote signature with a vote on it.
        yield sse_event(
            {
                "done": True,
                "signature": reply_signature(reply, help_signing_key(settings.service_secret)),
                "answer": {
                    "id": str(answer_id),
                    "trace_id": trace_id,
                    "signature": vote_signature(
                        answer_id, trace_id, help_signing_key(settings.service_secret)
                    ),
                },
            }
        )

    return event_stream(events())


@router.post("/contact", status_code=status.HTTP_204_NO_CONTENT)
async def contact(body: ContactRequest, request: Request) -> None:
    """The contact page's message; notifications emails it to prepza's inbox. Public, so the
    sender shows they're a person."""
    await require_human(request, settings.turnstile_secret_key)
    await contact_service.send(body, limit_address(request), request_language(request))
