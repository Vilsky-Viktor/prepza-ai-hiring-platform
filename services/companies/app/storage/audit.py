from datetime import UTC, datetime
from uuid import UUID, uuid4

from prepza_common.audit_actions import ACTION_GROUPS, MAX_TARGET_LABEL, AuditAction, TargetKind
from prepza_common.constants import DELETED_USER
from prepza_common.db import delete_in_batches
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError

from app.models.audit import AuditEvent
from app.service_auth import REQUEST_KEY, REQUEST_VIA
from app.storage.db import Session


def fields(
    company_id,
    user_id: str,
    action: str,
    target_id=None,
    via: str | None = None,
    target_kind: str | None = None,
    target_label: str | None = None,
) -> dict:
    """An action's columns: with the way the request came through (the assistant or an AI app)
    unless `via` says, and the API key it came with, if any."""
    key = REQUEST_KEY.get()

    return {
        "company_id": company_id,
        "user_id": user_id,
        "action": action,
        "group": ACTION_GROUPS[action],
        "target_kind": target_kind,
        "target_id": target_id,
        "target_label": target_label[:MAX_TARGET_LABEL] if target_label else None,
        "via": via or REQUEST_VIA.get(),
        "key_id": UUID(key) if key else None,
    }


def row(*args, **details) -> AuditEvent:
    """An action to add in the change's own transaction (fields)."""
    return AuditEvent(**fields(*args, **details))


async def record(company_id, user_id: str, action: str, target_id=None, **details) -> None:
    """An action, once its change is saved (row has the `details`)."""
    async with Session() as session:
        session.add(row(company_id, user_id, action, target_id, **details))
        await session.commit()


async def record_view(company_id, user_id: str, invite_id, via: str | None = None) -> None:
    """A member viewed a candidate's results: one row a member, candidate and UTC day, which a
    later view that day moves to its own time and way (the unique index makes two views at once
    one row too)."""
    values = fields(
        company_id,
        user_id,
        AuditAction.RESULTS_VIEWED,
        invite_id,
        via=via,
        target_kind=TargetKind.CANDIDATE,
    )
    now = datetime.now(UTC)
    query = insert(AuditEvent).values(id=uuid4(), **values, created_at=now, day=now.date())
    query = query.on_conflict_do_update(
        index_elements=["company_id", "user_id", "target_id", "day"],
        index_where=AuditEvent.action == AuditAction.RESULTS_VIEWED,
        set_={
            "created_at": query.excluded.created_at,
            "via": query.excluded.via,
            "key_id": query.excluded.key_id,
        },
    )

    async with Session() as session:
        await session.execute(query)
        await session.commit()


async def record_interview(interview, user_id: str, action: str, via: str | None = None) -> None:
    """An action on an interview, with its title as it is now, so it still reads once it's gone."""
    await record(
        interview.company_id,
        user_id,
        action,
        interview.id,
        via=via,
        target_kind=TargetKind.INTERVIEW,
        target_label=interview.title,
    )


async def store_event(event_id: str, data: dict, at: datetime) -> None:
    """Another service's action (prepza_common.audit), once however often it comes, at the time
    it happened. A company deleted since keeps nothing."""
    query = (
        insert(AuditEvent)
        .values(
            company_id=UUID(data["company_id"]),
            user_id=data["user_id"],
            action=data["action"],
            group=ACTION_GROUPS[data["action"]],
            target_kind=data.get("target_kind"),
            target_id=UUID(data["target_id"]) if data.get("target_id") else None,
            target_label=data.get("target_label"),
            removed=data.get("removed"),
            event_id=event_id,
            created_at=at,
        )
        .on_conflict_do_nothing(index_elements=["event_id"])
    )

    async with Session() as session:
        try:
            await session.execute(query)
            await session.commit()
        except IntegrityError:
            # The company is gone (its foreign key).
            await session.rollback()


async def list_for_company(
    company_id,
    offset: int,
    limit: int,
    user_id: str | None = None,
    group: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
) -> list[AuditEvent]:
    """Newest first; only one member's, one group's, or those from `start` and before `end`."""
    query = select(AuditEvent).where(AuditEvent.company_id == company_id)

    if user_id is not None:
        query = query.where(AuditEvent.user_id == user_id)

    if group is not None:
        query = query.where(AuditEvent.group == group)

    if start is not None:
        query = query.where(AuditEvent.created_at >= start)

    if end is not None:
        query = query.where(AuditEvent.created_at < end)

    query = query.order_by(AuditEvent.created_at.desc(), AuditEvent.id).offset(offset).limit(limit)

    async with Session() as session:
        return list(await session.scalars(query))


async def forget_user(user_id: str) -> None:
    """The user's actions stay in their companies' logs, without the user's id."""
    query = update(AuditEvent).where(AuditEvent.user_id == user_id).values(user_id=DELETED_USER)

    async with Session() as session:
        await session.execute(query)
        await session.commit()


async def delete_before(before: datetime) -> int:
    """Audit events from before `before`, deleted a batch at a time; how many."""
    return await delete_in_batches(Session, AuditEvent, AuditEvent.created_at < before)
