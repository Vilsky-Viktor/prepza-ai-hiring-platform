from uuid import UUID

from ats.repositories import ats_links
from ats.services import ats as integrations


async def handle(data: dict) -> None:
    """Workable's notifications for the interview's linked jobs are cancelled (as far as Workable
    answers), then its links and candidates go. Deleting twice deletes nothing more."""
    interview_id = UUID(data["interview_id"])

    for link, connection in await ats_links.interview_links(interview_id):
        if link.subscription_id:
            await integrations.unsubscribe(connection, [link.subscription_id])

    await ats_links.delete_interview(interview_id)
