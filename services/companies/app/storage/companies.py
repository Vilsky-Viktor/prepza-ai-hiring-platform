from datetime import UTC, datetime
from uuid import UUID

# Aliased: this module's own delete() would otherwise shadow it.
from prepza_common import outbox
from prepza_common.constants import LEGAL_VERSIONS
from sqlalchemy import String, and_, cast, func, literal, or_, select, update
from sqlalchemy import delete as sql_delete
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.constants.events import COMPANY_DELETED
from app.constants.roles import Role
from app.constants.verification import RENAME_REVIEWED, VerificationStatus
from app.core.exceptions import OverLimit
from app.models.companies import Company, Member
from app.models.interviews import Interview
from app.models.invites import CandidateInvite
from app.models.outbox import OutboxEvent
from app.storage import guests
from app.storage.db import Session

# The unique index on company names (see models/companies.py).
NAME_INDEX = "uq_companies_lower_name"


def owned_by(user_id: str):
    return (
        select(func.count())
        .select_from(Member)
        .where(Member.user_id == user_id, Member.role == Role.OWNER)
    )


async def lock_owner(session, user_id: str) -> int:
    """Holds the person's companies still until the transaction ends, so two requests can't both
    pass the count of what they own; returns that count."""
    await session.execute(select(func.pg_advisory_xact_lock(func.hashtext(f"owned:{user_id}"))))

    return await session.scalar(owned_by(user_id))


async def create(name: str, user_id: str, email: str, most: int | None = None) -> Company | None:
    """None when another company already has the name, in any case; the database decides, so
    two people creating the same name at once can't both get it. OverLimit when the person
    already owns `most` companies, counted under a lock (two creates at once can't both pass)."""
    company = Company(
        name=name,
        dpa_version=LEGAL_VERSIONS["dpa"],
        members=[Member(user_id=user_id, invited_email=email.lower(), role=Role.OWNER)],
    )

    async with Session() as session:
        owned = await lock_owner(session, user_id)

        if most is not None and owned >= most:
            raise OverLimit(owned)

        session.add(company)

        try:
            await session.commit()
        except IntegrityError as error:
            if NAME_INDEX in str(error.orig):
                return None

            raise

    return company


async def owned_count(user_id: str) -> int:
    async with Session() as session:
        return await session.scalar(owned_by(user_id))


async def ids_for_user(user_id: str) -> list[str]:
    """Every company the user is a member of."""
    query = select(Member.company_id).where(Member.user_id == user_id)

    async with Session() as session:
        return [str(company_id) for company_id in await session.scalars(query)]


async def get(company_id) -> Company | None:
    async with Session() as session:
        return await session.get(Company, company_id, options=[selectinload(Company.members)])


async def names(company_ids: list) -> dict:
    """Company names by id; deleted companies are missing."""
    if not company_ids:
        return {}

    query = select(Company.id, Company.name).where(Company.id.in_(company_ids))

    async with Session() as session:
        return {str(row.id): row.name for row in await session.execute(query)}


async def delete(company_id) -> None:
    """With the company.deleted event, which the outbox publishes until notifications has it."""
    async with Session() as session:
        # Its interviews' invites go with it (cascade).
        await guests.announce_deleted(
            session,
            CandidateInvite.interview_id.in_(
                select(Interview.id).where(Interview.company_id == company_id)
            ),
        )
        await session.execute(sql_delete(Company).where(Company.id == company_id))
        outbox.add(session, OutboxEvent, COMPANY_DELETED, {"company_id": str(company_id)})
        await session.commit()


async def list_for_user(
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

    async with Session() as session:
        return list((await session.scalars(query)).unique())


async def set_logo(company_id, content: bytes | None, media_type: str | None) -> None:
    """Saves the company's logo, or removes it with None; either way its address changes."""
    async with Session() as session:
        await session.execute(
            update(Company)
            .where(Company.id == company_id)
            .values(logo=content, logo_type=media_type, logo_version=Company.logo_version + 1)
        )
        await session.commit()


async def set_brand_colors(company_id, theme: str, colors: dict | None) -> None:
    """Saves the company's colors for one theme, or goes back to prepza's with None. In SQL, so
    two people saving the two themes at once both keep theirs."""
    saved = func.coalesce(Company.brand_colors, cast({}, JSONB))
    value = (
        saved.op("||")(cast({theme: colors}, JSONB))
        if colors
        else saved.op("-")(literal(theme, String))
    )

    async with Session() as session:
        await session.execute(
            update(Company).where(Company.id == company_id).values(brand_colors=value)
        )
        await session.commit()


async def set_brand_style(company_id, font: str, radius: int, button_radius: int) -> None:
    async with Session() as session:
        await session.execute(
            update(Company)
            .where(Company.id == company_id)
            .values(brand_font=font, brand_radius=radius, brand_button_radius=button_radius)
        )
        await session.commit()


async def get_logo(company_id) -> tuple[bytes, str] | None:
    async with Session() as session:
        row = (
            await session.execute(
                select(Company.logo, Company.logo_type).where(Company.id == company_id)
            )
        ).first()

    if row is None or row.logo is None:
        return None

    return row.logo, row.logo_type


async def rename(company_id, name: str) -> bool:
    """False when another company already has the name, in any case; the database decides. A
    company verified, waiting for review or declined loses its badge until a superadmin reviews
    the new name; its domain's proof still holds (a declined one only with a proof on file)."""
    async with Session() as session:
        try:
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
            await session.commit()
        except IntegrityError as error:
            if NAME_INDEX in str(error.orig):
                return False

            raise

    return True


async def set_ai_apps(company_id, allowed: bool) -> None:
    async with Session() as session:
        await session.execute(
            update(Company)
            .where(Company.id == company_id)
            .values(ai_apps_off_at=None if allowed else datetime.now(UTC))
        )
        await session.commit()
