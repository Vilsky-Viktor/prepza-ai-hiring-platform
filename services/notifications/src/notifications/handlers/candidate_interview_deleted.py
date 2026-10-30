from notifications.services import notes, notices


async def handle(data: dict, event_id: str) -> None:
    """The notifications about a deleted interview's candidates go, and its notes' (in the bell
    and the digest)."""
    await notices.remove_interview_candidates(data["company_id"], data["interview_id"])
    await notes.remove_interview(data["company_id"], data["interview_id"])
