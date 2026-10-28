from uuid import UUID

from ats.services import ats_candidates


async def handle(data: dict) -> None:
    """An interview's questions are ready: the candidates waiting for it are invited, each once
    (the claim)."""
    await ats_candidates.invite_waiting(UUID(data["interview_id"]))
