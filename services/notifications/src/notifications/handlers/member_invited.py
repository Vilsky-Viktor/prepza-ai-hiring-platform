from notifications.config import settings
from notifications.helpers.emails import member_invite_email
from notifications.services import events


async def handle(data: dict, event_id: str) -> None:
    """A member's invite to join a company."""
    await events.deliver(member_invite_email(data, settings.site_url), event_id)
