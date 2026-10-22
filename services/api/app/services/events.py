from datetime import UTC, datetime
from uuid import UUID

from app.constants.events import (
    CANDIDATE_EVENTS,
    CANDIDATE_INTERVIEW_DELETED,
    CANDIDATE_REMOVED,
    COMPANY_DELETED,
    INTERVIEW_READY,
)
from app.services import webhooks as webhook_events
from app.storage import keys, webhook_retries, webhooks


async def handle(
    event_type: str, data: dict, event_id: str, occurred_at: datetime | None = None
) -> None:
    """Companies' events, with when they happened (`occurred_at`, now when unknown). Each is safe
    to run again on a redelivery: a web hook gets an event once (its deliveries), and deleting
    twice deletes nothing more. Other events are ignored."""
    when = occurred_at or datetime.now(UTC)

    if event_type in CANDIDATE_EVENTS:
        await webhook_events.candidate_event(event_type, data, event_id, when)
    elif event_type == CANDIDATE_REMOVED:
        await webhook_retries.remove_candidate(
            UUID(data["company_id"]), data["interview_id"], data["email"]
        )
        # Sent from companies' newer events only, which say which candidate it was.
        if "candidate_invite_id" in data:
            await webhook_events.removed(data, event_id, when)
    elif event_type == CANDIDATE_INTERVIEW_DELETED:
        await webhook_retries.remove_interview(UUID(data["company_id"]), data["interview_id"])
    elif event_type == INTERVIEW_READY:
        # Sent from companies' newer events only, which say whose interview it is.
        if "company_id" in data:
            await webhook_events.interview_ready(data, event_id, when)
    elif event_type == COMPANY_DELETED:
        company_id = UUID(data["company_id"])
        await keys.remove_company(company_id)
        await webhooks.remove_company(company_id)
