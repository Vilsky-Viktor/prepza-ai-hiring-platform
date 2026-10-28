from fastapi import APIRouter, HTTPException, Path, Query, Request, status
from fastapi.responses import PlainTextResponse
from prepza_common.auth.human_check import require_human
from prepza_common.auth.user import Language
from prepza_common.config.constants import DEFAULT_LANGUAGE, LEGAL_VERSIONS
from prepza_common.http.client_ip import limit_address
from prepza_common.i18n.i18n import request_language

from site_content.config import settings
from site_content.constants.help import (
    MAX_GUIDE_SLUG_LENGTH,
    MAX_PAGE_KEY_LENGTH,
    NO_SUCH_GUIDE,
    NO_SUCH_PAGE,
    PAGE_ARTICLES,
    PRICES_UNAVAILABLE,
    LegalDocument,
)
from site_content.constants.legal import NO_SUCH_VERSION
from site_content.helpers import legal
from site_content.helpers.guide_articles import guide_article, guide_articles
from site_content.helpers.help import faq_items
from site_content.helpers.page_guides import page_guide
from site_content.integrations import billing
from site_content.schemas.contact import ContactRequest
from site_content.schemas.help import (
    FaqItemOut,
    GuideItemOut,
    GuideOut,
    LegalOut,
    PageGuideOut,
)
from site_content.services import contact as contact_service
from site_content.services.help import platform_guide

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
    """Everything prepza's help chat (in the assistant) answers from, as text: how prepza works and how to use it,
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


@router.post("/contact", status_code=status.HTTP_204_NO_CONTENT)
async def contact(body: ContactRequest, request: Request) -> None:
    """The contact page's message; notifications emails it to prepza's inbox. Public, so the
    sender shows they're a person."""
    await require_human(request, settings.turnstile_secret_key)
    await contact_service.send(body, limit_address(request), request_language(request))
