from accounts.services.guest_events import delete_guests


async def handle(event_id: str, data: dict) -> None:
    """Deleted guest invites' guests: their sign-ins and what accounts kept under them go."""
    await delete_guests(event_id, data)
