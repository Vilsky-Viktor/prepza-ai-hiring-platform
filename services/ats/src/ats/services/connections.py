from uuid import UUID

from ats.core.db import Session
from ats.repositories import ats, ats_links
from ats.services import ats as integrations
from ats.services import outbox as outbox_service


async def save(
    company_id: UUID,
    provider: str,
    account: str,
    sealed: str,
    user_id: str,
    member_id: str | None = None,
    language: str | None = None,
) -> None:
    """Saves the company's connection, with its action log entry, and sends that entry."""
    async with Session.begin() as session:
        await ats.connect(
            session, company_id, provider, account, sealed, user_id, member_id, language
        )

    await outbox_service.flush_quietly()


async def disconnect(company_id: UUID, provider: str, user_id: str) -> None:
    """Workable's notifications and Breezy HR's web hook are cancelled (as far as each answers),
    then the key is deleted, and its linked jobs with it."""
    async with Session() as session:
        connection = await ats.connection(session, company_id, provider)
        subscriptions = await ats_links.subscriptions(session, company_id) if connection else []

    if connection is not None:
        await integrations.release(connection, subscriptions)

    async with Session.begin() as session:
        await ats.disconnect(session, company_id, provider, user_id)

    await outbox_service.flush_quietly()


async def save_webhook_key(company_id: UUID, provider: str, secret: str) -> None:
    """Saves the secret key the ATS made for the company's web hook: its events count from then
    on."""
    connection = await integrations.connected(company_id, provider)
    found = await integrations.credentials(connection)
    sealed = integrations.seal({**found, "webhook_secret": secret})

    async with Session.begin() as session:
        await ats.set_credentials(session, connection.id, sealed)
