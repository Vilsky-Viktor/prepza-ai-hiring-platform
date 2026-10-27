import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from prepza_common.auth.superadmin import SuperadminUser

from app.constants.invites import COMPANY_NAME_TAKEN
from app.constants.superadmin import COMPANIES_SHOWN
from app.schemas.superadmin_companies import CompanyNameIn, SuperadminCompanyOut
from app.services import company_deletion
from app.storage import companies, superadmin_companies

# The admin zone's companies tab: superadmins step in for impersonation or abuse. Each step goes
# to the logs with who took it.
router = APIRouter(prefix="/superadmin/companies", tags=["superadmin"])
logger = logging.getLogger(__name__)


@router.get("")
async def list_companies(
    superadmin: SuperadminUser, q: Annotated[str, Query(max_length=200)] = ""
) -> list[SuperadminCompanyOut]:
    """Companies by name, newest first, at most COMPANIES_SHOWN."""
    return [
        SuperadminCompanyOut(
            id=company.id,
            name=company.name,
            verification_status=company.verification_status,
            verified_domain=company.verified_domain,
            members=members,
            suspended=company.suspended_at is not None,
            created_at=company.created_at,
        )
        for company, members in await superadmin_companies.search(q.strip(), COMPANIES_SHOWN)
    ]


async def suspend(company_id: UUID, suspended: bool, superadmin_id: str) -> None:
    if not await superadmin_companies.set_suspended(company_id, suspended):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Company not found")

    action = "suspended" if suspended else "unsuspended"
    logger.warning("Company %s %s by superadmin %s", company_id, action, superadmin_id)


@router.post("/{company_id}/suspend", status_code=status.HTTP_204_NO_CONTENT)
async def suspend_company(company_id: UUID, superadmin: SuperadminUser) -> None:
    """Nothing new happens for the company: its members can read but not change it, it invites
    nobody, and candidates who haven't started find its interviews unavailable."""
    await suspend(company_id, True, superadmin.uid)


@router.post("/{company_id}/unsuspend", status_code=status.HTTP_204_NO_CONTENT)
async def unsuspend_company(company_id: UUID, superadmin: SuperadminUser) -> None:
    await suspend(company_id, False, superadmin.uid)


@router.put("/{company_id}/name", status_code=status.HTTP_204_NO_CONTENT)
async def rename_company(company_id: UUID, body: CompanyNameIn, superadmin: SuperadminUser) -> None:
    """Frees a name an impersonator took; a name taken by another company is a 409."""
    if await companies.get(company_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Company not found")

    if not await companies.rename(company_id, body.name.strip()):
        raise HTTPException(status.HTTP_409_CONFLICT, COMPANY_NAME_TAKEN)

    logger.warning("Company %s renamed by superadmin %s", company_id, superadmin.uid)


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(company_id: UUID, superadmin: SuperadminUser) -> None:
    """As its owner deleting it: everything goes, its interviews, candidates and credits."""
    if await companies.get(company_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Company not found")

    await company_deletion.delete_company(company_id)
    logger.warning("Company %s deleted by superadmin %s", company_id, superadmin.uid)
