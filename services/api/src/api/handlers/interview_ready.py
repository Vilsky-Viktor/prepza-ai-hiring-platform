from datetime import datetime

from api.services import webhooks


async def handle(data: dict, event_id: str, occurred_at: datetime) -> None:
    """An interview's questions are ready: the company's web hooks hear it, each once."""
    # Sent from companies' newer events only, which say whose interview it is.
    if "company_id" in data:
        await webhooks.interview_ready(data, event_id, occurred_at)
