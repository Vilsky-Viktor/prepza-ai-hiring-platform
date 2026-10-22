from uuid import UUID

from prepza_common import audit
from prepza_common.audit_actions import AuditAction, TargetKind
from prepza_common.db import delete_in_batches
from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert

from app.constants.ats import CandidateStatus
from app.models.ats import AtsCandidate, AtsConnection, AtsJobLink
from app.models.outbox import OutboxEvent
from app.storage.ats import company_of
from app.storage.db import Session


async def links(company_id: UUID) -> list[tuple[AtsJobLink, str]]:
    """The company's linked jobs, newest first, each with its ATS."""
    query = (
        select(AtsJobLink, AtsConnection.provider)
        .join(AtsConnection, AtsConnection.id == AtsJobLink.connection_id)
        .where(AtsConnection.company_id == company_id)
        .order_by(AtsJobLink.created_at.desc())
    )

    async with Session() as session:
        return [tuple(row) for row in (await session.execute(query)).all()]


async def add_link(
    company_id: UUID,
    connection_id: UUID,
    interview_id: UUID,
    job: dict,
    stage: dict,
    user_id: str,
) -> UUID | None:
    """Links a job to an interview: the link's id, or None when that job is already linked. The
    company's action log gets it as the member's (`user_id`)."""
    query = (
        insert(AtsJobLink)
        .values(
            connection_id=connection_id,
            company_id=company_of(connection_id),
            interview_id=interview_id,
            job_id=job["id"],
            job_name=job["name"],
            stage_id=stage["id"],
            stage_name=stage["name"],
        )
        .on_conflict_do_nothing(index_elements=["connection_id", "job_id"])
        .returning(AtsJobLink.id)
    )

    async with Session() as session:
        added = await session.scalar(query)

        if added is not None:
            audit.add(
                session,
                OutboxEvent,
                company_id,
                user_id,
                AuditAction.JOB_LINKED,
                TargetKind.INTEGRATION,
                target_label=job["name"],
            )

        await session.commit()

    return added


async def set_subscription(link_id: UUID, subscription_id: str) -> None:
    query = (
        update(AtsJobLink).where(AtsJobLink.id == link_id).values(subscription_id=subscription_id)
    )

    async with Session() as session:
        await session.execute(query)
        await session.commit()


async def link(link_id: UUID) -> tuple[AtsJobLink, AtsConnection] | None:
    """A linked job with its connection: where an ATS event for it is checked."""
    query = (
        select(AtsJobLink, AtsConnection)
        .join(AtsConnection, AtsConnection.id == AtsJobLink.connection_id)
        .where(AtsJobLink.id == link_id)
    )

    async with Session() as session:
        row = (await session.execute(query)).first()

        return tuple(row) if row else None


async def interview_links(interview_id: UUID) -> list[tuple[AtsJobLink, AtsConnection]]:
    """The jobs linked to an interview, each with its connection: what to cancel in the ATS
    when the interview goes."""
    query = (
        select(AtsJobLink, AtsConnection)
        .join(AtsConnection, AtsConnection.id == AtsJobLink.connection_id)
        .where(AtsJobLink.interview_id == interview_id)
    )

    async with Session() as session:
        return [tuple(row) for row in (await session.execute(query)).all()]


async def link_for_job(connection_id: UUID, job_id: str) -> AtsJobLink | None:
    query = select(AtsJobLink).where(
        AtsJobLink.connection_id == connection_id, AtsJobLink.job_id == job_id
    )

    async with Session() as session:
        return await session.scalar(query)


async def has_links(connection_id: UUID) -> bool:
    query = select(AtsJobLink.id).where(AtsJobLink.connection_id == connection_id).limit(1)

    async with Session() as session:
        return await session.scalar(query) is not None


async def subscriptions(company_id: UUID, link_id: UUID | None = None) -> list[str]:
    """The ATS notifications of the company's linked jobs (or of one), to cancel them."""
    query = (
        select(AtsJobLink.subscription_id)
        .join(AtsConnection, AtsConnection.id == AtsJobLink.connection_id)
        .where(AtsConnection.company_id == company_id, AtsJobLink.subscription_id.is_not(None))
    )

    if link_id is not None:
        query = query.where(AtsJobLink.id == link_id)

    async with Session() as session:
        return list((await session.scalars(query)).all())


async def remove_link(company_id: UUID, link_id: UUID, user_id: str) -> bool:
    """Unlinks a job of the company; False when there's no such link. Its candidates still
    waiting go with it, so nothing invites them (or sets credits aside for them) any more; the
    invited ones stay, for writing their results back. The company's action log gets it as the
    member's (`user_id`)."""
    owned = select(AtsConnection.id).where(AtsConnection.company_id == company_id)
    query = (
        delete(AtsJobLink)
        .where(AtsJobLink.id == link_id, AtsJobLink.connection_id.in_(owned))
        .returning(AtsJobLink.job_name)
    )

    async with Session() as session:
        removed = await session.scalar(query)

        if removed is not None:
            audit.add(
                session,
                OutboxEvent,
                company_id,
                user_id,
                AuditAction.JOB_UNLINKED,
                TargetKind.INTEGRATION,
                target_label=removed,
            )
            await session.execute(
                delete(AtsCandidate).where(
                    AtsCandidate.link_id.is_(None),
                    AtsCandidate.status == CandidateStatus.WAITING,
                    AtsCandidate.connection_id.in_(owned),
                )
            )

        await session.commit()

    return removed is not None


async def delete_interview(interview_id: UUID) -> None:
    """An interview was deleted: the candidates sent for it go, DELETE_BATCH at a time, each
    batch its own transaction, then its linked jobs. Safe to repeat."""
    await delete_in_batches(Session, AtsCandidate, AtsCandidate.interview_id == interview_id)

    async with Session() as session:
        await session.execute(delete(AtsJobLink).where(AtsJobLink.interview_id == interview_id))
        await session.commit()
