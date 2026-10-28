"""An owner or admin's changes to the company itself: its name, its brand (logo, colors,
style) and whether AI apps may use its data. Each is saved with its line in the action log."""

import asyncio
import base64
import binascii

from fastapi import HTTPException, status
from prepza_common.auth.auth import CurrentUser
from prepza_common.events.audit_actions import AuditAction, TargetKind
from sqlalchemy.exc import IntegrityError

from companies.constants.ai_apps import AI_APPS_CHANGED_BY_APP
from companies.constants.invites import COMPANY_NAME_TAKEN
from companies.core.db import Session
from companies.helpers.brand import unreadable
from companies.helpers.logos import logo_path, logo_type, stored_logo
from companies.models.companies import Company
from companies.repositories import audit, companies
from companies.services.access import require_editor


async def changed(company_id, user_id: str, action: str, change, *args, **details) -> None:
    """Runs the repository's `change(session, company_id, *args)` and records `action` on the
    company, in one save."""
    async with Session.begin() as session:
        await change(session, company_id, *args)
        await audit.record(
            session,
            company_id,
            user_id,
            action,
            company_id,
            target_kind=TargetKind.COMPANY,
            **details,
        )


async def rename(company: Company, user_id: str, title: str) -> None:
    """Names stay unique across prepza, ignoring case (409)."""
    name = title.strip()

    if not name:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Name the company")

    if name == company.name:
        return

    try:
        await changed(
            company.id,
            user_id,
            AuditAction.COMPANY_RENAMED,
            companies.rename,
            name,
            target_label=name,
        )
    except IntegrityError as error:
        if companies.name_taken(error):
            raise HTTPException(status.HTTP_409_CONFLICT, COMPANY_NAME_TAKEN) from None

        raise


async def set_ai_apps(company_id, user: CurrentUser, allowed: bool, via: str | None) -> None:
    """Owners and admins allow, or stop, members using the company's data from the AI apps they
    connected. Never through an AI app or the assistant (403, before anything else): a person
    decides, in prepza itself."""
    if via is not None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, AI_APPS_CHANGED_BY_APP)

    company, _ = await require_editor(user, company_id)
    await changed(
        company.id, user.uid, AuditAction.AI_APPS_CHANGED, companies.set_ai_apps, allowed, via=via
    )


async def set_logo(company: Company, user_id: str, image: str) -> str | None:
    """A PNG, JPEG or WebP image up to 500 KB, base64 (422 otherwise); its new address."""
    try:
        content = base64.b64decode(image, validate=True)
    except binascii.Error:
        content = b""

    media_type = logo_type(content)

    # Decoding is CPU work, kept off the event loop.
    stored = await asyncio.to_thread(stored_logo, content, media_type) if media_type else None

    if stored is None:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "Use a PNG, JPEG or WebP image up to 500 KB"
        )

    await changed(company.id, user_id, AuditAction.LOGO_CHANGED, companies.set_logo, *stored)

    async with Session() as session:
        return logo_path(await companies.get(session, company.id))


async def remove_logo(company: Company, user_id: str) -> None:
    await changed(company.id, user_id, AuditAction.LOGO_CHANGED, companies.set_logo, None, None)


async def set_brand_colors(company: Company, user_id: str, theme: str, colors: dict | None) -> None:
    """Colors that would make any text hard to read are refused (422), so no candidate is
    tested on a page they can't read; none goes back to prepza's."""
    problem = unreadable(colors) if colors else None

    if problem:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, problem)

    await changed(
        company.id, user_id, AuditAction.BRAND_CHANGED, companies.set_brand_colors, theme, colors
    )


async def set_brand_style(
    company: Company, user_id: str, font: str, radius: int, button_radius: int
) -> None:
    await changed(
        company.id,
        user_id,
        AuditAction.BRAND_CHANGED,
        companies.set_brand_style,
        font,
        radius,
        button_radius,
    )
