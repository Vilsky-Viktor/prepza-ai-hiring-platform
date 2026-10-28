from ats.services import ats_candidates


async def handle(data: dict) -> None:
    """A candidate finished: their results go back to the ATS that sent them, once
    (reported_at)."""
    await ats_candidates.report(data)
