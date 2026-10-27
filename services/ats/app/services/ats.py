import asyncio
import json
import logging

from cryptography.fernet import Fernet
from fastapi import HTTPException, status
from prepza_common.auth.encryption import decrypt, encrypt
from prepza_common.limits.rate_limit import hit_or_skip

from app.config.settings import settings
from app.constants.ats import (
    ATS_ACTION_SECONDS,
    ATS_NAMES,
    WORKABLE_WEBHOOK,
    WRITES,
    AtsProvider,
)
from app.integrations import breezy, workable
from app.integrations.ats_clients import client
from app.integrations.ats_http import calling_company
from app.integrations.errors import KeyRejected, WriteRefused
from app.integrations.redis import get_redis
from app.models.ats import AtsConnection
from app.services import outbox as outbox_service
from app.storage import ats


def available() -> bool:
    """Whether integrations are set up here: a valid encryption key."""
    try:
        Fernet(settings.ats_encryption_key)
    except ValueError:
        return False

    return True


async def count_connect(company_id, user_id: str) -> None:
    """Counts one connection made or replaced: each is checked with a call to the ATS."""
    key = f"rate:ats-connects:{company_id}"
    who = {"company_id": company_id, "user_id": user_id}
    await hit_or_skip(get_redis(), key, "ATS_CONNECTS_PER_HOUR", **who)


async def count_call(company_id, user_id: str) -> None:
    """Counts one page's call to the company's ATS (or the invites a retry sends), once the
    caller may make it: against floods, so with Redis down not counted."""
    key = f"rate:ats-calls:{company_id}"
    who = {"company_id": company_id, "user_id": user_id}
    await hit_or_skip(get_redis(), key, "ATS_CALLS_PER_COMPANY_MINUTE", **who)


def require_available() -> None:
    if not available():
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Integrations aren't set up")


def seal(credentials: dict) -> str:
    return encrypt(settings.ats_encryption_key, json.dumps(credentials))


async def credentials(connection: AtsConnection) -> dict:
    """The connection's credentials, as its ATS's client takes them. A key that can't be read
    any more (the encryption key changed) marks the connection broken, like one the ATS
    refuses. Its ATS's rate limit hits from here on are the connection's company's."""
    calling_company.set(connection.company_id)
    opened = decrypt(settings.ats_encryption_key, connection.credentials)

    if opened is None:
        await broken(connection)

    return json.loads(opened)


async def workable_key(connection: AtsConnection) -> tuple[str, str]:
    """A Workable connection's subdomain and token, for what only Workable has (subscriptions,
    signed events)."""
    found = await credentials(connection)

    return found["subdomain"], found["token"]


async def broken(connection: AtsConnection) -> None:
    """Marks the connection for reconnecting, and tells the company."""
    await ats.mark_broken(connection.id)
    await outbox_service.flush_quietly()
    name = ATS_NAMES[connection.provider]

    raise HTTPException(
        status.HTTP_409_CONFLICT, f"{name} no longer accepts the key: reconnect to continue"
    )


async def connected(company_id, provider: str) -> AtsConnection:
    require_available()
    connection = await ats.connection(company_id, provider)

    if connection is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not connected")

    return connection


async def call(connection: AtsConnection, action: str, **arguments):
    """One action of the connection's ATS client (integrations/ats_clients.py), with its
    credentials; a refused key marks the connection broken. A refused write (WRITES) while the
    key still reads is a key without write access: WriteRefused, and the connection keeps
    inviting. An ATS doesn't always say which it is (Workable answers 401 to both). The whole
    action ends within ATS_ACTION_SECONDS: past it, the ATS didn't answer (502)."""
    found = await credentials(connection)
    used = client(connection.provider)
    keys = {key: found[key] for key in used.KEYS}

    try:
        async with asyncio.timeout(ATS_ACTION_SECONDS):
            return await getattr(used, action)(**keys, **arguments)
    except TimeoutError:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, used.UNAVAILABLE) from None
    except KeyRejected:
        if action in WRITES and await still_reads(used, keys):
            raise WriteRefused from None

        await broken(connection)


async def still_reads(used, keys: dict) -> bool:
    try:
        await used.check(**keys)
    except KeyRejected:
        return False

    return True


async def jobs(connection: AtsConnection) -> list[dict]:
    return await call(connection, "jobs")


async def stages(connection: AtsConnection, job_id: str) -> list[dict]:
    return await call(connection, "stages", job_id=job_id)


async def job(connection: AtsConnection, job_id: str) -> dict:
    return await call(connection, "job", job_id=job_id)


async def subscribe(connection: AtsConnection, link_id, job_id: str, stage_id: str) -> str:
    """Asks Workable to send this link's candidates (moved into the stage) to its own address."""
    subdomain, token = await workable_key(connection)
    target = WORKABLE_WEBHOOK.format(site=settings.site_url, link_id=link_id)

    try:
        return await workable.subscribe(subdomain, token, target, job_id, stage_id)
    except KeyRejected:
        await broken(connection)


async def remove_webhook(connection: AtsConnection) -> None:
    """Deletes the web hook prepza created in Breezy HR for the connection, as far as Breezy
    answers: the connection goes either way, and events for it are ignored after."""
    if connection.provider != AtsProvider.BREEZY:
        return

    try:
        found = await credentials(connection)

        if found.get("webhook_id"):
            await breezy.unsubscribe(found["company"], found["token"], found["webhook_id"])
    except (HTTPException, KeyRejected):
        logging.getLogger(__name__).warning(
            "Couldn't delete the Breezy web hook of connection %s", connection.id
        )


async def release(connection: AtsConnection, subscription_ids: list[str]) -> None:
    """What prepza set up in the ATS for a connection that goes (Workable's notifications,
    Breezy HR's web hook): cancelled as far as the ATS answers."""
    await unsubscribe(connection, subscription_ids)
    await remove_webhook(connection)


async def unsubscribe(connection: AtsConnection, subscription_ids: list[str]) -> None:
    """Cancels Workable's notifications, as far as Workable answers: a link or connection goes
    either way, and events for it are ignored after. Only a Workable connection has them."""
    if connection.provider != AtsProvider.WORKABLE:
        return

    for subscription_id in subscription_ids:
        try:
            subdomain, token = await workable_key(connection)
            await workable.unsubscribe(subdomain, token, subscription_id)
        except (HTTPException, KeyRejected):
            logging.getLogger(__name__).warning(
                "Couldn't cancel Workable subscription %s", subscription_id
            )
