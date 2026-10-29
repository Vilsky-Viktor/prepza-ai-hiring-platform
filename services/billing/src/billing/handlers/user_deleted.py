from datetime import datetime

from prepza_common.events.deletions import UserDeleted

from billing.services import accounts


async def handle(data: dict, event_id: str, occurred_at: datetime) -> None:
    """A user deleted their account: the automatic top-ups paid with their card are cancelled
    and go off, their purchases for their companies stay without them, their currency goes, and
    their AI costs and limit hits stay without them. Safe to repeat: a cancelled subscription
    counts as cancelled, and nothing is left to forget."""
    await accounts.delete_user(UserDeleted.model_validate(data).user_id)
