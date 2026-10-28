from uuid import UUID

from assistant.services import conversations


async def handle(company_id: UUID, data: dict) -> int:
    """A company erased a candidate: its conversations that mention them (their email or
    invite) go. Returns how many."""
    needles = [str(data.get("email") or ""), str(data.get("candidate_invite_id") or "")]

    return await conversations.delete_mentioning(company_id, needles)
