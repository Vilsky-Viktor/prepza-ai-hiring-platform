from uuid import UUID

from assistant.services import conversations


async def handle(company_id: UUID, data: dict) -> int:
    """A company was deleted: its conversations go. Returns how many."""
    return await conversations.delete_company(company_id)
