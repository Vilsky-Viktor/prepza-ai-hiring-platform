from datetime import UTC, datetime
from uuid import UUID

from prepza_common.config.constants import LEGAL_VERSIONS
from prepza_common.events.deletions import COMPANY_DELETED, CompanyDeleted
from sqlalchemy import String, and_, cast, func, literal, or_, select, update

# Aliased: this module's own delete() would otherwise shadow it.
from sqlalchemy import delete as sql_delete
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from companies.constants.roles import Role
from companies.constants.verification import RENAME_REVIEWED, VerificationStatus
from companies.core.exceptions import OverLimit
from companies.models.companies import Company, Member
from companies.models.invites import CandidateInvite
from companies.repositories import guests, outbox

# The unique index on company names (see models/companies.py).
NAME_INDEX = "uq_companies_lower_name"


def owned_by(user_id: str):
    return (
        select(func.count())
        .select_from(Member)
        .where(Member.user_id == user_id, Member.role == Role.OWNER)
    )


async def lock_owner(session: AsyncSession, user_id: str) -> int:
    """Holds the person's companies still until the transaction ends, so two requests can't both
    pass the count of what they own; returns that count."""
    await session.execute(select(func.pg_advisory_xact_lock(func.hashtext(f"owned:{user_id}"))))

    return await session.scalar(owned_by(user_id))


def name_taken(error: IntegrityError) -> bool:
    """Whether a write failed because another company has the name, in any case."""
    return NAME_INDEX in str(error.orig)


async def create(
    session: AsyncSession, name: str, user_id: str, email: str, most: int | None = None
) -> Company:
    """An IntegrityError when another company already has the name, in any case (name_taken);
    the database decides, so two people creating the same name at once can't both get it.
    OverLimit when the person already owns `most` companies, counted under a lock (two creates
    at once can't both pass)."""
    company = Company(
        name=name,
        dpa_version=LEGAL_VERSIONS["dpa"],
        members=[Member(user_id=user_id, invited_email=email.lower(), role=Role.OWNER)],
    )

    owned = await lock_owner(session, user_id)

    if most is not None and owned >= most:
        raise OverLimit(owned)

    session.add(company)
    await session.flush()

    return company


async def owned_count(session: AsyncSession, user_id: str) -> int:
    return await session.scalar(owned_by(user_id))


async def ids_for_user(session: AsyncSession, user_id: str) -> list[str]:
    """Every company the user is a member of."""
    query = select(Member.company_id).where(Member.user_id == user_id)

    return [str(company_id) for company_id in await session.scalars(query)]


async def get(session: AsyncSession, company_id) -> Company | None:
    return await session.get(Company, company_id, options=[selectinload(Company.members)])


async def names(session: AsyncSession, company_ids: list) -> dict:
    """Company names by id; deleted companies are missing."""
    if not company_ids:
        return {}

    query = select(Company.id, Company.name).where(Company.id.in_(company_ids))

    return {str(row.id): row.name for row in await session.execute(query)}


async def delete(session: AsyncSession, company_id) -> None:
    """The company, with its members and the company.deleted event, which the outbox publishes
    until Pub/Sub has it (rounds and library delete what they keep of it); its invites, action log and interviews went first (a batch at a
    time: services/batch_deletion.py)."""
    # An invite made meanwhile goes with the company (cascade).
    await guests.announce_deleted(session, CandidateInvite.company_id == company_id)
    await session.execute(sql_delete(Company).where(Company.id == company_id))
    outbox.add(
        session, COMPANY_DELETED, CompanyDeleted(company_id=company_id).model_dump(mode="json")
    )


async def list_for_user(
    session: AsyncSession,
    user_id: str,
    offset: int,
    limit: int,
    roles: tuple[str, ...] = tuple(Role),
    only: str | None = None,
) -> list[Company]:
    """The user's companies, by name (alphabetically, in any case), only those where their role is
    one of `roles` (and with `only`, that one company's id at most)."""
    query = (
        select(Company)
        .join(Member, Member.company_id == Company.id)
        .where(Member.user_id == user_id, Member.role.in_(roles))
        .options(selectinload(Company.members))
        .order_by(func.lower(Company.name), Company.id)
        .offset(offset)
        .limit(limit)
    )

    if only is not None:
        query = query.where(Company.id == UUID(only))

    return list((await session.scalars(query)).unique())


async def set_logo(
    session: AsyncSession, company_id, content: bytes | None, media_type: str | None
) -> None:
    """Saves the company's logo, or removes it with None; either way its address changes."""
    await session.execute(
        update(Company)
        .where(Company.id == company_id)
        .values(logo=content, logo_type=media_type, logo_version=Company.logo_version + 1)
    )


async def set_brand_colors(
    session: AsyncSession, company_id, theme: str, colors: dict | None
) -> None:
    """Saves the company's colors for one theme, or goes back to prepza's with None. In SQL, so
    two people saving the two themes at once both keep theirs."""
    saved = func.coalesce(Company.brand_colors, cast({}, JSONB))
    value = (
        saved.op("||")(cast({theme: colors}, JSONB))
        if colors
        else saved.op("-")(literal(theme, String))
    )

    await session.execute(
        update(Company).where(Company.id == company_id).values(brand_colors=value)
    )


async def set_brand_style(
    session: AsyncSession, company_id, font: str, radius: int, button_radius: int
) -> None:
    await session.execute(
        update(Company)
        .where(Company.id == company_id)
        .values(brand_font=font, brand_radius=radius, brand_button_radius=button_radius)
    )


async def get_logo(session: AsyncSession, company_id) -> tuple[bytes, str] | None:
    row = (
        await session.execute(
            select(Company.logo, Company.logo_type).where(Company.id == company_id)
        )
    ).first()

    if row is None or row.logo is None:
        return None

    return row.logo, row.logo_type


async def rename(session: AsyncSession, company_id, name: str) -> None:
    """An IntegrityError when another company already has the name, in any case (name_taken);
    the database decides. A company verified, waiting for review or declined loses its badge
    until a superadmin reviews the new name; its domain's proof still holds (a declined one only
    with a proof on file)."""
    await session.execute(update(Company).where(Company.id == company_id).values(name=name))
    await session.execute(
        update(Company)
        .where(
            Company.id == company_id,
            or_(
                Company.verification_status.in_(RENAME_REVIEWED),
                and_(
                    Company.verification_status == VerificationStatus.DECLINED,
                    Company.verification_email.is_not(None),
                ),
            ),
        )
        .values(
            verified_domain=None,
            verification_status=VerificationStatus.PENDING,
            verification_name=name,
            verification_submitted_at=datetime.now(UTC),
            decline_reason=None,
            verification_decided_by=None,
            verification_decided_at=None,
        )
    )


async def set_ai_apps(session: AsyncSession, company_id, allowed: bool) -> None:
    await session.execute(
        update(Company)
        .where(Company.id == company_id)
        .values(ai_apps_off_at=None if allowed else datetime.now(UTC))
    )
