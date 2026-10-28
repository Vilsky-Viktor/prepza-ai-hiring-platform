from uuid import UUID

from ats.services import accounts


async def handle(data: dict) -> None:
    """Workable's notifications for the interview's linked jobs are cancelled (as far as Workable
    answers), then its links and candidates go. Deleting twice deletes nothing more."""
    await accounts.remove_interview(UUID(data["interview_id"]))
