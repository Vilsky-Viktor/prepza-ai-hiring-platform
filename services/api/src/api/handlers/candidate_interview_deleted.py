from uuid import UUID

from api.repositories import webhook_retries


async def handle(data: dict) -> None:
    """A company deleted an interview: its candidates' results waiting to be sent again go."""
    await webhook_retries.remove_interview(UUID(data["company_id"]), data["interview_id"])
