from testee_common.events.deletions import UserDeleted

from notifications.services import accounts


async def handle(data: dict, event_id: str) -> None:
    """A user deleted their account: their notifications, sent log and bulk-send rows go, and
    companies' notifications about them; the Slack channels they connected stay without them,
    each company told once (a redelivery finds none left to forget)."""
    event = UserDeleted.model_validate(data)
    await accounts.remove_user(event.user_id, event.email)
