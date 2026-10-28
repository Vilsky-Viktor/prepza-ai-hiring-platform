from library.services.guest_events import delete_guests


async def handle(event_id: str, data: dict) -> None:
    """Deleted guest invites' guests: what library kept under their sign-ins goes too."""
    await delete_guests(event_id, data)
