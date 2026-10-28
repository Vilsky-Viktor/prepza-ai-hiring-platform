from uuid import UUID

from fastapi import HTTPException, status

from ats.constants.ats import ATS_NAMES, AtsProvider, CandidateStatus
from ats.core.db import Session
from ats.integrations import companies
from ats.repositories import ats_candidates, ats_links
from ats.schemas.ats import JobLinkIn, JobLinkOut
from ats.services import ats as integrations
from ats.services import outbox as outbox_service


async def links(company_id: UUID) -> list[JobLinkOut]:
    """The company's linked jobs, newest first, with their interviews' titles (from companies)
    and how many of their candidates are in each status."""
    async with Session() as session:
        counts = await ats_candidates.counts(session, company_id)
        found = await ats_links.links(session, company_id)

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


async def job_and_stage(connection, body: JobLinkIn) -> tuple[dict, dict]:
    """The job and stage as the ATS has them now, read for the one job, which also checks they
    exist (a job deleted in the ATS answers 404)."""
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

    return job, stage


async def add(company_id: UUID, body: JobLinkIn, user_id: str) -> None:
    """Links an ATS job to one of the company's interviews: its candidates who reach the stage
    will get the interview. A job has one interview. Workable is then asked to send candidates
    moved into the stage; a link it won't notify isn't kept (unlinked again as the member's, so
    the action log shows the link didn't stay). Greenhouse and the others send them through the
    web hook the company set up."""
    connection = await integrations.connected(company_id, body.provider)
    interview = (await companies.interviews([body.interview_id])).get(body.interview_id)

    # Also an interview still being made, as "new interview from this job" links it at once;
    # candidates are invited once it's ready.
    if interview is None or UUID(interview["company_id"]) != company_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Interview not found")

    job, stage = await job_and_stage(connection, body)

    async with Session.begin() as session:
        link_id = await ats_links.add_link(
            session, company_id, connection.id, body.interview_id, job, stage, user_id
        )

    await outbox_service.flush_quietly()

    if link_id is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "That job is already linked")

    if body.provider != AtsProvider.WORKABLE:
        return

    try:
        subscription = await integrations.subscribe(connection, link_id, job["id"], stage["id"])
    except Exception:
        async with Session.begin() as session:
            await ats_links.remove_link(session, company_id, link_id, user_id)

        await outbox_service.flush_quietly()
        raise

    async with Session.begin() as session:
        await ats_links.set_subscription(session, link_id, subscription)


async def remove(company_id: UUID, link_id: UUID, user_id: str) -> None:
    """Unlinks a job of the company: Workable's notifications for it are cancelled first, as far
    as Workable answers."""
    async with Session() as session:
        found = await ats_links.link(session, link_id)
        mine = found is not None and found[1].company_id == company_id
        subscriptions = await ats_links.subscriptions(session, company_id, link_id) if mine else []

    if mine:
        await integrations.unsubscribe(found[1], subscriptions)

    async with Session.begin() as session:
        removed = await ats_links.remove_link(session, company_id, link_id, user_id)

    if not removed:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Link not found")

    await outbox_service.flush_quietly()
