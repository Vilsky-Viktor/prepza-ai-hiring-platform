"""A superadmin's steps on a company, for impersonation or abuse; each goes to the logs with
who took it."""

import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from companies.constants.invites import COMPANY_NAME_TAKEN
from companies.core.db import Session
from companies.repositories import companies, superadmin_companies
from companies.services import company_deletion

logger = logging.getLogger(__name__)


async def found(company_id: UUID) -> None:
    """404 when there's no such company."""
    async with Session() as session:
        company = await companies.get(session, company_id)

    if company is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Company not found")


async def suspend(company_id: UUID, suspended: bool, superadmin_id: str) -> None:
    async with Session.begin() as session:
        changed = await superadmin_companies.set_suspended(session, company_id, suspended)

    if not changed:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Company not found")

    action = "suspended" if suspended else "unsuspended"
    logger.warning("Company %s %s by superadmin %s", company_id, action, superadmin_id)


async def rename(company_id: UUID, name: str, superadmin_id: str) -> None:
    """Frees a name an impersonator took; a name taken by another company is a 409."""
    await found(company_id)

    try:
        async with Session.begin() as session:
            await companies.rename(session, company_id, name)
    except IntegrityError as error:
        if companies.name_taken(error):
            raise HTTPException(status.HTTP_409_CONFLICT, COMPANY_NAME_TAKEN) from None

        raise

    logger.warning("Company %s renamed by superadmin %s", company_id, superadmin_id)


async def delete(company_id: UUID, superadmin_id: str) -> None:
    """As its owner deleting it: everything goes, its interviews, candidates and credits."""
    await found(company_id)
    await company_deletion.delete_company(company_id)
    logger.warning("Company %s deleted by superadmin %s", company_id, superadmin_id)
