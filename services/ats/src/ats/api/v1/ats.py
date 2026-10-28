from uuid import UUID

from fastapi import APIRouter, status
from prepza_common.auth.auth import CurrentUser
from prepza_common.config.constants import MAX_GOAL_LENGTH

from ats.constants.ats import AtsProvider
from ats.core.db import Session
from ats.helpers.ats import job_text
from ats.integrations import companies
from ats.repositories import ats
from ats.schemas.ats import (
    AtsItemOut,
    ConnectionOut,
    IntegrationsOut,
    JobLinkIn,
    JobLinkOut,
    JobTextOut,
)
from ats.services import ats as integrations
from ats.services import ats_candidates as ats_candidates_service
from ats.services import connections, links

router = APIRouter(tags=["ats"])


@router.get("/connections")
async def list_connections(company_id: UUID, user: CurrentUser) -> IntegrationsOut:
    """The company's ATS connections; every member sees them, only owners and admins change
    them."""
    await companies.require(company_id, user.uid)

    async with Session() as session:
        rows = await ats.connections(session, company_id)

    return IntegrationsOut(
        available=integrations.available(),
        connections=[
            ConnectionOut(
                provider=row.provider,
                account=row.account,
                status=row.status,
                created_at=row.created_at,
            )
            for row in rows
        ],
    )


@router.delete("/{provider}", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect(company_id: UUID, provider: AtsProvider, user: CurrentUser) -> None:
    """Disconnects: Workable's notifications and Breezy HR's web hook are cancelled, then the key
    is deleted, and its linked jobs with it."""
    await companies.require(company_id, user.uid, editor=True)
    await connections.disconnect(company_id, provider, user.uid)


@router.get("/{provider}/jobs")
async def list_jobs(company_id: UUID, provider: AtsProvider, user: CurrentUser) -> list[AtsItemOut]:
    await companies.require(company_id, user.uid, editor=True)
    await integrations.count_call(company_id, user.uid)
    connection = await integrations.connected(company_id, provider)

    return [AtsItemOut(**job) for job in await integrations.jobs(connection)]


@router.get("/{provider}/jobs/{job_id}/stages")
async def list_stages(
    company_id: UUID, provider: AtsProvider, job_id: str, user: CurrentUser
) -> list[AtsItemOut]:
    await companies.require(company_id, user.uid, editor=True)
    await integrations.count_call(company_id, user.uid)
    connection = await integrations.connected(company_id, provider)

    return [AtsItemOut(**stage) for stage in await integrations.stages(connection, job_id)]


@router.get("/{provider}/jobs/{job_id}/text")
async def job_text_of(
    company_id: UUID, provider: AtsProvider, job_id: str, user: CurrentUser
) -> JobTextOut:
    """A job's title, description, requirements and benefits as plain text, to make an
    interview from (the same limit as a pasted job description)."""
    await companies.require(company_id, user.uid, editor=True)
    await integrations.count_call(company_id, user.uid)
    connection = await integrations.connected(company_id, provider)
    found = await integrations.job(connection, job_id)

    return JobTextOut(text=job_text(found["name"], found["sections"], MAX_GOAL_LENGTH))


@router.get("/links")
async def list_links(company_id: UUID, user: CurrentUser) -> list[JobLinkOut]:
    await companies.require(company_id, user.uid)

    return await links.links(company_id)


@router.post("/links", status_code=status.HTTP_201_CREATED)
async def add_link(company_id: UUID, body: JobLinkIn, user: CurrentUser) -> None:
    """Links an ATS job to one of the company's interviews: its candidates who reach the stage
    will get the interview. A job has one interview."""
    await companies.require(company_id, user.uid, editor=True)
    await integrations.count_call(company_id, user.uid)
    await links.add(company_id, body, user.uid)


@router.delete("/links/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_link(company_id: UUID, link_id: UUID, user: CurrentUser) -> None:
    await companies.require(company_id, user.uid, editor=True)
    await integrations.count_call(company_id, user.uid)
    await links.remove(company_id, link_id, user.uid)


@router.post("/links/{link_id}/retry", status_code=status.HTTP_204_NO_CONTENT)
async def retry_candidates(company_id: UUID, link_id: UUID, user: CurrentUser) -> None:
    """Invites again the candidates the ATS sent for this job who weren't invited (after a
    top-up, or once the pause is off)."""
    await companies.require(company_id, user.uid, editor=True)
    await integrations.count_call(company_id, user.uid)
    await ats_candidates_service.retry(company_id, link_id)
