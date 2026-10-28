from ats.services import reports


async def handle(data: dict) -> None:
    """A candidate finished: their results go back to the ATS that sent them, once
    (reported_at)."""
    await reports.report(data)
