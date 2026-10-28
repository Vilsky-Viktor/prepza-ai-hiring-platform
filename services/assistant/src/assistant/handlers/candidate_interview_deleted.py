from uuid import UUID

from assistant.repositories import conversations


async def handle(company_id: UUID, data: dict) -> int:
    """A company deleted an interview with its candidates: its conversations that mention the
    interview go. Returns how many."""
    needles = [str(data.get("interview_id") or "")]

    return await conversations.delete_mentioning(company_id, needles)
