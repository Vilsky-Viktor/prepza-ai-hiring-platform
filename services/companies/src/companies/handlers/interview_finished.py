from datetime import datetime

from companies.services import candidate_billing


async def handle(data: dict, event_id: str, at: datetime) -> None:
    """A candidate finished: the company is charged (or gets the credits back) and told once."""
    await candidate_billing.finish(data, event_id)
