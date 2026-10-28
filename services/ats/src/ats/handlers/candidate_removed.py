from uuid import UUID

from ats.repositories import ats_candidates


async def handle(data: dict) -> None:
    """A company erased a candidate: its ATS record of them goes. Deleting twice deletes nothing
    more."""
    await ats_candidates.delete_candidate(UUID(data["interview_id"]), data["email"])
