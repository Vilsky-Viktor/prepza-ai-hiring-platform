from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status
from prepza_common.auth.auth import CurrentUser

from companies.constants.brand import PREPZA_COLORS, Theme
from companies.constants.logos import LOGO_CACHE
from companies.core.db import Session
from companies.repositories import companies
from companies.schemas.logos import (
    BrandColorSets,
    BrandColorsIn,
    BrandColorsOut,
    BrandOut,
    BrandStyle,
    LogoIn,
    LogoOut,
    PrepzaBrand,
)
from companies.services import company_settings, invite_pages
from companies.services.access import require_editor

# Company branding: the logo candidates see on their pages, emails and reports, and the colors
# of their pages.
router = APIRouter(tags=["logos"])


@router.put("/companies/{company_id}/logo")
async def set_logo(company_id: UUID, body: LogoIn, user: CurrentUser) -> LogoOut:
    """Any of the company's owners and admins sets the logo: PNG, JPEG or WebP, up to 500 KB."""
    company, _ = await require_editor(user, company_id)

    return LogoOut(logo_url=await company_settings.set_logo(company, user.uid, body.image))


@router.delete("/companies/{company_id}/logo", status_code=status.HTTP_204_NO_CONTENT)
async def remove_logo(company_id: UUID, user: CurrentUser) -> None:
    company, _ = await require_editor(user, company_id)
    await company_settings.remove_logo(company, user.uid)


@router.get("/brand/prepza")
async def prepza_brand() -> PrepzaBrand:
    """prepza's own colors (by theme), fonts and rounding: where a company's start, and what they
    go back to."""
    return PrepzaBrand(colors=BrandColorSets(**PREPZA_COLORS), style=BrandStyle())


@router.put("/companies/{company_id}/brand-colors/{theme}")
async def set_brand_colors(
    company_id: UUID, theme: Theme, body: BrandColorsIn, user: CurrentUser
) -> BrandColorsOut:
    """Any of the company's owners and admins sets its colors for one theme, or goes back to
    prepza's with none. Colors that would make any text hard to read are refused, so no
    candidate is tested on a page they can't read."""
    company, _ = await require_editor(user, company_id)
    colors = body.colors.model_dump() if body.colors else None
    await company_settings.set_brand_colors(company, user.uid, theme, colors)

    return BrandColorsOut(colors=body.colors)


@router.put("/companies/{company_id}/brand-style")
async def set_brand_style(company_id: UUID, body: BrandStyle, user: CurrentUser) -> BrandStyle:
    """Any of the company's owners and admins sets the fonts (titles and text) and corner
    rounding of its candidates' pages, the same in both themes."""
    company, _ = await require_editor(user, company_id)
    await company_settings.set_brand_style(company, user.uid, body.model_dump())

    return body


@router.get("/companies/{company_id}/logo")
async def get_logo(company_id: UUID) -> Response:
    """Public: candidates' pages and email clients load it without signing in."""
    async with Session() as session:
        found = await companies.get_logo(session, company_id)

    if found is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No logo")

    content, media_type = found

    return Response(
        content,
        media_type=media_type,
        headers={"Cache-Control": LOGO_CACHE, "X-Content-Type-Options": "nosniff"},
    )


@router.get("/candidates/{invite_id}/brand")
async def candidate_brand(invite_id: UUID, user: CurrentUser) -> BrandOut:
    """The company and logo for the candidate taking the interview, or a member previewing it."""
    return await invite_pages.brand(invite_id, user)
