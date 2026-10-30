"""What a candidate's pages show before and while they take a test: their invite, a test's
shareable link, and the company's brand."""

from uuid import UUID

from fastapi import HTTPException, status
from prepza_common.auth.user import User

from companies.core.db import Session
from companies.helpers.allowed_domains import frame_sources
from companies.helpers.brand import color_sets, style_of
from companies.helpers.candidates import candidate_seconds, takes_voice
from companies.helpers.interviews import interview_minutes
from companies.helpers.invite_links import addressed_to
from companies.helpers.logos import logo_path
from companies.helpers.return_urls import with_invite
from companies.models.interviews import Interview
from companies.repositories import companies, interviews, invites
from companies.schemas.invites import InviteView, LinkView
from companies.schemas.logos import BrandColorSets, BrandOut, BrandStyle
from companies.services import set_cache
from companies.services.access import open_invite, refuse_if_suspended
from companies.services.interview_views import attach_set, interview_title


async def company_of(interview: Interview):
    async with Session() as session:
        return await companies.get(session, interview.company_id)


async def invite_view(
    token: str,
    user: User | None,
    embed_origin: str | None = None,
    embed_referrer: str | None = None,
) -> InviteView:
    """The invitation, also before signing in; whether it's the signed-in account's, and its
    email only to that account with the email verified. For a guest invite, who may frame it:
    the company's allowed domains, unless the page embedding it is elsewhere (frame_sources)."""
    # An expired invite's link stops working until the company sends it again.
    invite, interview = await open_invite(token)
    interview = await attach_set(interview)
    title = await interview_title(interview)

    company = await company_of(interview)
    refuse_if_suspended(company, invite.status)
    seconds = candidate_seconds(interview.question_seconds, invite.extra_time)
    found = await set_cache.get_set(interview.set_id) if interview.set_id else None
    matches, email = addressed_to(user, invite.email)
    # Their own mode when the company set one, else the interview's.
    voice = takes_voice(invite, interview)

    return InviteView(
        interview_id=interview.id,
        title=title,
        company=company.name if company else "",
        logo_url=logo_path(company),
        verified_domain=company.verified_domain if company else None,
        email=email,
        matches=matches,
        status=invite.status,
        question_seconds=seconds,
        total_minutes=interview_minutes(found, interview.topic_limits, seconds),
        voice=voice,
        guest=invite.guest,
        brand_colors=BrandColorSets(**color_sets(company.brand_colors if company else None)),
        theme=invite.theme,
        brand_style=BrandStyle(**style_of(company)),
        embed_domain=company.verified_domain if company and invite.guest else None,
        embed_ancestors=frame_sources(
            company.allowed_domains, company.allow_localhost, embed_origin, embed_referrer
        )
        if company and invite.guest
        else [],
    )


async def linked_interview(token: str) -> Interview:
    """The interview a shareable link opens; 404 when the link is off or wrong."""
    async with Session() as session:
        interview = await interviews.get_by_link(session, token)

    if interview is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Link not found")

    return interview


async def link_view(token: str, user: User | None) -> LinkView:
    """The test behind a shareable link. Signed in with a verified email, it also says how far
    they got; an unverified one could claim anyone's address, so it learns nothing about that
    person."""
    interview = await attach_set(await linked_interview(token))
    verified = user is not None and user.email_verified

    async with Session() as session:
        company = await companies.get(session, interview.company_id)
        status_now = (
            await invites.status_of(session, interview.id, user.email) if verified else None
        )

    refuse_if_suspended(company, status_now)
    found = await set_cache.get_set(interview.set_id) if interview.set_id else None

    return LinkView(
        title=await interview_title(interview),
        company=company.name if company else "",
        logo_url=logo_path(company),
        verified_domain=company.verified_domain if company else None,
        brand_colors=BrandColorSets(**color_sets(company.brand_colors if company else None)),
        brand_style=BrandStyle(**style_of(company)),
        question_seconds=interview.question_seconds,
        total_minutes=interview_minutes(found, interview.topic_limits, interview.question_seconds),
        voice=bool(interview.voice),
        status=status_now,
    )


async def brand(invite_id: UUID, user: User) -> BrandOut:
    """The company and logo for the candidate taking the interview, or a member previewing it;
    404 for anyone else."""
    async with Session() as session:
        invite = await invites.get(session, invite_id)
        interview = await interviews.get(session, invite.interview_id) if invite else None
        company = await companies.get(session, interview.company_id) if interview else None

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
