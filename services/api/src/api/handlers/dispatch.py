from datetime import UTC, datetime

from api.constants.events import (
    CANDIDATE_EVENTS,
    CANDIDATE_INTERVIEW_DELETED,
    CANDIDATE_REMOVED,
    COMPANY_DELETED,
    INTERVIEW_READY,
)
from api.handlers import (
    candidate_interview_deleted,
    candidate_progress,
    candidate_removed,
    company_deleted,
    interview_ready,
)


async def handle(
    event_type: str, data: dict, event_id: str, occurred_at: datetime | None = None
) -> None:
    """Companies' events, each to its handler, with when they happened (`occurred_at`, now when
    unknown). Each is safe to run again on a redelivery: a web hook gets an event once (its
    deliveries), and deleting twice deletes nothing more. Other events are ignored."""
    when = occurred_at or datetime.now(UTC)

    if event_type in CANDIDATE_EVENTS:
        await candidate_progress.handle(event_type, data, event_id, when)
    elif event_type == CANDIDATE_REMOVED:
        await candidate_removed.handle(data, event_id, when)
    elif event_type == CANDIDATE_INTERVIEW_DELETED:
        await candidate_interview_deleted.handle(data)
    elif event_type == INTERVIEW_READY:
        await interview_ready.handle(data, event_id, when)
    elif event_type == COMPANY_DELETED:
        await company_deleted.handle(data)
