from prepza_common.limits.rate_limit import hit

from rounds.constants.events import CONTACT_SENT
from rounds.core.db import Session
from rounds.integrations.redis import get_redis
from rounds.repositories import sessions
from rounds.schemas.contact import ContactRequest
from rounds.services import outbox as outbox_service


async def send(body: ContactRequest, address: str, language: str) -> None:
    """Keeps the contact page's message as an event until it's published; notifications emails
    it to prepza's inbox. Limited per address and in all."""
    redis = get_redis()
    await hit(redis, f"rate:contact:ip:{address}", "CONTACT_IP_LIMIT")
    await hit(redis, "rate:contact:all", "CONTACT_DAILY_LIMIT")

    async with Session.begin() as session:
        await sessions.add_event(session, CONTACT_SENT, {**body.model_dump(), "language": language})

    await outbox_service.flush_quietly()
