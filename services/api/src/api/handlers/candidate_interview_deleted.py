from uuid import UUID

from api.services import accounts


async def handle(data: dict) -> None:
    """A company deleted an interview: its candidates' results waiting to be sent again go."""
    await accounts.remove_interview(UUID(data["company_id"]), data["interview_id"])
