from notifications.config import settings
from notifications.helpers.emails import contact_email
from notifications.services import events


async def handle(data: dict, event_id: str) -> None:
    """A contact page message, emailed to prepza's inbox."""
    await events.deliver(contact_email(data, settings.contact_email), event_id)
