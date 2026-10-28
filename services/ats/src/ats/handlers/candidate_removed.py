from uuid import UUID

from ats.services import accounts


async def handle(data: dict) -> None:
    """A company erased a candidate: its ATS record of them goes. Deleting twice deletes nothing
    more."""
    await accounts.remove_candidate(UUID(data["interview_id"]), data["email"])
