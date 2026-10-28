from notifications.services import notices


async def handle(data: dict, event_id: str) -> None:
    """An erased candidate's notifications go."""
    await notices.remove_candidate(data["email"], data["company_id"])
