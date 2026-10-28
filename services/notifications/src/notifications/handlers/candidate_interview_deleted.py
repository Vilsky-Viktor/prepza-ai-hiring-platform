from notifications.repositories import notifications


async def handle(data: dict, event_id: str) -> None:
    """The notifications about a deleted interview's candidates go."""
    await notifications.remove_interview_candidates(data["company_id"], data["interview_id"])
