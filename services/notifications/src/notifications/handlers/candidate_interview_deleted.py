from notifications.services import notices


async def handle(data: dict, event_id: str) -> None:
    """The notifications about a deleted interview's candidates go."""
    await notices.remove_interview_candidates(data["company_id"], data["interview_id"])
