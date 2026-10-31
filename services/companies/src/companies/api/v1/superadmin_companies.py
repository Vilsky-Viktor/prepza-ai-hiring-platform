from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status
from testee_common.auth.superadmin import SuperadminUser

from companies.constants.superadmin import COMPANIES_SHOWN
from companies.core.db import Session
from companies.repositories import superadmin_companies as superadmin_store
from companies.schemas.superadmin_companies import CompanyNameIn, SuperadminCompanyOut
from companies.services import superadmin_companies

# The admin zone's companies tab: superadmins step in for impersonation or abuse. Each step goes
# to the logs with who took it.
router = APIRouter(prefix="/superadmin/companies", tags=["superadmin"])


@router.get("")
async def list_companies(
    superadmin: SuperadminUser, q: Annotated[str, Query(max_length=200)] = ""
) -> list[SuperadminCompanyOut]:
    """Companies by name, newest first, at most COMPANIES_SHOWN."""
    async with Session() as session:
        found = await superadmin_store.search(session, q.strip(), COMPANIES_SHOWN)

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
        for company, members in found
    ]


@router.post("/{company_id}/suspend", status_code=status.HTTP_204_NO_CONTENT)
async def suspend_company(company_id: UUID, superadmin: SuperadminUser) -> None:
    """Nothing new happens for the company: its members can read but not change it, it invites
    nobody, and candidates who haven't started find its interviews unavailable."""
    await superadmin_companies.suspend(company_id, True, superadmin.uid)


@router.post("/{company_id}/unsuspend", status_code=status.HTTP_204_NO_CONTENT)
async def unsuspend_company(company_id: UUID, superadmin: SuperadminUser) -> None:
    await superadmin_companies.suspend(company_id, False, superadmin.uid)


@router.put("/{company_id}/name", status_code=status.HTTP_204_NO_CONTENT)
async def rename_company(company_id: UUID, body: CompanyNameIn, superadmin: SuperadminUser) -> None:
    """Frees a name an impersonator took; a name taken by another company is a 409."""
    await superadmin_companies.rename(company_id, body.name.strip(), superadmin.uid)


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(company_id: UUID, superadmin: SuperadminUser) -> None:
    """As its owner deleting it: everything goes, its interviews, candidates and credits."""
    await superadmin_companies.delete(company_id, superadmin.uid)
