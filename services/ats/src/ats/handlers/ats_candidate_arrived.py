from ats.services import ats_candidates


async def handle(data: dict) -> None:
    """An ATS's web hook sent a new candidate, saved: they're invited, once (the claim)."""
    await ats_candidates.invite_arrived(data)
