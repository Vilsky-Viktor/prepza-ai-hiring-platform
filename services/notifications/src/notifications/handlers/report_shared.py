from notifications.config import settings
from notifications.helpers.emails import report_email
from notifications.services import events


async def handle(data: dict, event_id: str) -> None:
    """A candidate's PDF report, emailed by a company member."""
    await events.deliver(report_email(data, settings.site_url), event_id)
