from datetime import datetime
from uuid import UUID

from api.repositories import webhook_retries
from api.services import webhooks


async def handle(data: dict, event_id: str, occurred_at: datetime) -> None:
    """A company erased a candidate: their results waiting to be sent again go, and its web hooks
    hear which candidate it was. Deleting twice deletes nothing more."""
    await webhook_retries.remove_candidate(
        UUID(data["company_id"]), data["interview_id"], data["email"]
    )

    # Sent from companies' newer events only, which say which candidate it was.
    if "candidate_invite_id" in data:
        await webhooks.removed(data, event_id, occurred_at)
