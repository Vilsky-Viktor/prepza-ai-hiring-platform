from datetime import datetime

from sqlalchemy.exc import IntegrityError

from companies.core.db import Session
from companies.repositories import audit


async def record(event_id: str, data: dict, at: datetime) -> None:
    """Stores another service's action in its company's log, once however often the event comes,
    at the time it happened (`at`, its outbox row's) however late it arrives. A company deleted
    since keeps nothing."""
    try:
        async with Session.begin() as session:
            await audit.store_event(session, event_id, data, at)
    except IntegrityError:
        # The company is gone (its foreign key).
        pass
