from testee_common.limits.rate_limit import hit

from site_content.constants.events import CONTACT_SENT
from site_content.core.db import Session
from site_content.integrations.redis import get_redis
from site_content.repositories import outbox
from site_content.schemas.contact import ContactRequest
from site_content.services import outbox as outbox_service


async def send(body: ContactRequest, address: str, language: str) -> None:
    """Keeps the contact page's message as an event until it's published; notifications emails
    it to testee's inbox. Limited per address and in all."""
    redis = get_redis()
    await hit(redis, f"rate:contact:ip:{address}", "CONTACT_IP_LIMIT")
    await hit(redis, "rate:contact:all", "CONTACT_DAILY_LIMIT")

    async with Session.begin() as session:
        outbox.add(session, CONTACT_SENT, {**body.model_dump(), "language": language})

    await outbox_service.flush_quietly()
