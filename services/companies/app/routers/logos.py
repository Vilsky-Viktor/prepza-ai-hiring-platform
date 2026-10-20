import asyncio
import base64
import binascii
from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status
from prepza_common.audit_actions import AuditAction, TargetKind
from prepza_common.auth import CurrentUser

from app.constants.brand import PREPZA_COLORS, Theme
from app.constants.logos import LOGO_CACHE
from app.helpers.brand import color_sets, style_of, unreadable
from app.helpers.logos import for_email, logo_path, logo_type
from app.helpers.return_urls import with_invite
from app.schemas.logos import (
    BrandColorSets,
    BrandColorsIn,
    BrandColorsOut,
    BrandOut,
    BrandStyle,
    LogoIn,
    LogoOut,
    PrepzaBrand,
)
from app.services.access import require_editor
from app.storage import audit, companies, interviews, invites

# Company branding: the logo candidates see on their pages, emails and reports, and the colors
# of their pages.
router = APIRouter(tags=["logos"])


@router.put("/companies/{company_id}/logo")
async def set_logo(company_id: UUID, body: LogoIn, user: CurrentUser) -> LogoOut:
    """Any of the company's owners and admins sets the logo: PNG, JPEG or WebP, up to 500 KB."""
    company, _ = await require_editor(user, company_id)

    try:
        content = base64.b64decode(body.image, validate=True)
    except binascii.Error:
        content = b""

    media_type = logo_type(content)

    # Decoding a WebP is CPU work, kept off the event loop.
    stored = await asyncio.to_thread(for_email, content, media_type) if media_type else None

    if stored is None:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "Use a PNG, JPEG or WebP image up to 500 KB"
        )

    await companies.set_logo(company.id, *stored)
    await audit.record(
        company.id, user.uid, AuditAction.LOGO_CHANGED, company.id, target_kind=TargetKind.COMPANY
    )

    return LogoOut(logo_url=logo_path(await companies.get(company.id)))


@router.delete("/companies/{company_id}/logo", status_code=status.HTTP_204_NO_CONTENT)
async def remove_logo(company_id: UUID, user: CurrentUser) -> None:
    company, _ = await require_editor(user, company_id)
    await companies.set_logo(company.id, None, None)
    await audit.record(
        company.id, user.uid, AuditAction.LOGO_CHANGED, company.id, target_kind=TargetKind.COMPANY
    )


@router.get("/brand/prepza")
async def prepza_brand() -> PrepzaBrand:
    """prepza's own colors (by theme), font and rounding: where a company's start, and what they
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
    problem = unreadable(colors) if colors else None

    if problem:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, problem)

    await companies.set_brand_colors(company.id, theme, colors)
    await audit.record(
        company.id, user.uid, AuditAction.BRAND_CHANGED, company.id, target_kind=TargetKind.COMPANY
    )

    return BrandColorsOut(colors=body.colors)


@router.put("/companies/{company_id}/brand-style")
async def set_brand_style(company_id: UUID, body: BrandStyle, user: CurrentUser) -> BrandStyle:
    """Any of the company's owners and admins sets the font and corner rounding of its
    candidates' pages, the same in both themes."""
    company, _ = await require_editor(user, company_id)
    await companies.set_brand_style(company.id, body.font, body.radius, body.button_radius)
    await audit.record(
        company.id, user.uid, AuditAction.BRAND_CHANGED, company.id, target_kind=TargetKind.COMPANY
    )

    return body


@router.get("/companies/{company_id}/logo")
async def get_logo(company_id: UUID) -> Response:
    """Public: candidates' pages and email clients load it without signing in."""
    found = await companies.get_logo(company_id)

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
    invite = await invites.get(invite_id)
    interview = await interviews.get(invite.interview_id) if invite else None
    company = await companies.get(interview.company_id) if interview else None
    member = company and any(item.user_id == user.uid for item in company.members)

    if company is None or (invite.user_id != user.uid and not member):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")

    back = invite.return_url if invite.user_id == user.uid else None

    return BrandOut(
        company=company.name,
        logo_url=logo_path(company),
        return_url=with_invite(back, invite.id) if back else None,
        brand_colors=BrandColorSets(**color_sets(company.brand_colors)),
        theme=invite.theme,
        brand_style=BrandStyle(**style_of(company)),
    )
