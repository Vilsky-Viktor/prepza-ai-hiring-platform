from notifications.repositories import notifications


async def handle(data: dict, event_id: str) -> None:
    """An erased candidate's notifications go."""
    await notifications.remove_candidate(data["email"], data["company_id"])
