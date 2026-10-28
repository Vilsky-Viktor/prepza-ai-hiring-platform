from library.services.copy_fixes import fix_copies


async def handle(event_id: str, data: dict) -> None:
    """A fixed bank question: its copies that still hold the old content get the new one."""
    await fix_copies(data)
