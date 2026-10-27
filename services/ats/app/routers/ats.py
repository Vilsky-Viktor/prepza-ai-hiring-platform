from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from prepza_common.auth.auth import CurrentUser
from prepza_common.config.constants import MAX_GOAL_LENGTH

from app.constants.ats import ATS_NAMES, AtsProvider, CandidateStatus
from app.helpers.ats import job_text
from app.integrations import companies
from app.schemas.ats import (
    AtsItemOut,
    ConnectionOut,
    IntegrationsOut,
    JobLinkIn,
    JobLinkOut,
    JobTextOut,
)
from app.services import ats as integrations
from app.services import ats_candidates as ats_candidates_service
from app.services import outbox as outbox_service
from app.storage import ats, ats_candidates, ats_links

router = APIRouter(tags=["ats"])


@router.get("/connections")
async def list_connections(company_id: UUID, user: CurrentUser) -> IntegrationsOut:
    """The company's ATS connections; every member sees them, only owners and admins change
    them."""
    await companies.require(company_id, user.uid)
    rows = await ats.connections(company_id)

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
    connection = await ats.connection(company_id, provider)

    if connection is not None:
        await integrations.release(connection, await ats_links.subscriptions(company_id))

    await ats.disconnect(company_id, provider, user.uid)
    await outbox_service.flush_quietly()


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
    counts = await ats_candidates.counts(company_id)
    found = await ats_links.links(company_id)
    interviews = await companies.interviews({link.interview_id for link, _ in found})

    return [
        JobLinkOut(
            id=link.id,
            provider=provider,
            job_name=link.job_name,
            stage_name=link.stage_name,
            interview_id=link.interview_id,
            interview_title=interviews.get(link.interview_id, {}).get("title"),
            invited=counts.get(link.id, {}).get(CandidateStatus.INVITED, 0),
            # Including an invite underway: one cut off midway shows here to invite again.
            not_invited=counts.get(link.id, {}).get(CandidateStatus.FAILED, 0)
            + counts.get(link.id, {}).get(CandidateStatus.INVITING, 0),
            waiting=counts.get(link.id, {}).get(CandidateStatus.WAITING, 0),
        )
        for link, provider in found
    ]


@router.post("/links", status_code=status.HTTP_201_CREATED)
async def add_link(company_id: UUID, body: JobLinkIn, user: CurrentUser) -> None:
    """Links an ATS job to one of the company's interviews: its candidates who reach the stage
    will get the interview. A job has one interview."""
    await companies.require(company_id, user.uid, editor=True)
    await integrations.count_call(company_id, user.uid)
    connection = await integrations.connected(company_id, body.provider)
    interview = (await companies.interviews([body.interview_id])).get(body.interview_id)

    # Also an interview still being made, as "new interview from this job" links it at once;
    # candidates are invited once it's ready.
    if interview is None or UUID(interview["company_id"]) != company_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Interview not found")

    # The names as the ATS has them now, read for the one job, which also checks the job and
    # stage exist (a job deleted in the ATS answers 404).
    try:
        found = await integrations.job(connection, body.job_id)
        job = {"id": body.job_id, "name": found["name"]}
        stage_list = await integrations.stages(connection, body.job_id)
    except HTTPException as error:
        if error.status_code != status.HTTP_404_NOT_FOUND:
            raise

        job, stage_list = None, []

    stage = next((stage for stage in stage_list if stage["id"] == body.stage_id), None)

    if job is None or stage is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"That job or stage isn't in {ATS_NAMES[body.provider]}"
        )

    link_id = await ats_links.add_link(
        company_id, connection.id, body.interview_id, job, stage, user.uid
    )
    await outbox_service.flush_quietly()

    if link_id is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "That job is already linked")

    # Workable is asked to send candidates moved into the stage; a link it won't notify isn't
    # kept. Greenhouse sends them through the web hook the company set up.
    if body.provider != AtsProvider.WORKABLE:
        return

    try:
        subscription = await integrations.subscribe(connection, link_id, job["id"], stage["id"])
    except Exception:
        # Unlinked again as the member's, so the action log shows the link didn't stay.
        await ats_links.remove_link(company_id, link_id, user.uid)
        await outbox_service.flush_quietly()
        raise

    await ats_links.set_subscription(link_id, subscription)


@router.delete("/links/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_link(company_id: UUID, link_id: UUID, user: CurrentUser) -> None:
    await companies.require(company_id, user.uid, editor=True)
    await integrations.count_call(company_id, user.uid)
    found = await ats_links.link(link_id)

    if found is not None and found[1].company_id == company_id:
        await integrations.unsubscribe(found[1], await ats_links.subscriptions(company_id, link_id))

    if not await ats_links.remove_link(company_id, link_id, user.uid):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Link not found")

    await outbox_service.flush_quietly()


@router.post("/links/{link_id}/retry", status_code=status.HTTP_204_NO_CONTENT)
async def retry_candidates(company_id: UUID, link_id: UUID, user: CurrentUser) -> None:
    """Invites again the candidates the ATS sent for this job who weren't invited (after a
    top-up, or once the pause is off)."""
    await companies.require(company_id, user.uid, editor=True)
    await integrations.count_call(company_id, user.uid)
    await ats_candidates_service.retry(company_id, link_id)
