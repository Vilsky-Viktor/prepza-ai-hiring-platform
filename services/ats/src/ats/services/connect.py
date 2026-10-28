import json
import secrets
from uuid import UUID

from fastapi import HTTPException, status
from prepza_common.auth.encryption import decrypt
from prepza_common.auth.user import User

from ats.config import settings
from ats.constants.ats import BREEZY_WEBHOOK, GREENHOUSE_CANT_WRITE, RECRUITEE_DOMAIN, AtsProvider
from ats.core.db import Session
from ats.helpers.ats import subdomain, verified_email
from ats.integrations import breezy, greenhouse, recruitee, teamtailor, workable
from ats.integrations.ats_http import calling_company
from ats.integrations.errors import KeyRejected
from ats.models.ats import AtsConnection
from ats.repositories import ats
from ats.schemas.ats import BreezyIn, GreenhouseIn, RecruiteeIn, TeamtailorIn, WorkableIn
from ats.services import ats as integrations
from ats.services import connections
from ats.services import outbox as outbox_service

# Connecting each ATS: its key is checked with the ATS first, then saved (connections.save);
# Breezy HR's web hook is created after.


async def kept_secret(company_id: UUID, provider: AtsProvider) -> str | None:
    """The web hook secret key of the connection a reconnect replaces, so its web hook goes on
    working. None when there's none, or its key can't be read any more (the encryption key
    changed): the reconnect then starts afresh."""
    async with Session() as session:
        earlier = await ats.connection(session, company_id, provider)

    opened = decrypt(settings.ats_encryption_key, earlier.credentials) if earlier else None

    return json.loads(opened).get("webhook_secret") if opened else None


async def connect_workable(company_id: UUID, body: WorkableIn, user: User) -> None:
    """Connects Workable with an account's API access token, checked with one read first. A
    second connect replaces the key."""
    integrations.require_available()
    account = subdomain(body.account, ".workable.com")

    if account is None:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Enter your Workable address, like acme.workable.com",
        )

    # Counted once the address could be right: a mistyped one is refused before.
    await integrations.count_connect(company_id, user.uid)
    calling_company.set(company_id)

    token = body.token.strip()

    try:
        await workable.check(account, token)
    except KeyRejected:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Workable didn't accept this token for that account",
        ) from None

    credentials = integrations.seal({"subdomain": account, "token": token})
    # Who results are written back as: the connecting user's Workable member, or an admin.
    member = await workable.member_id(account, token, verified_email(user))
    await connections.save(
        company_id, AtsProvider.WORKABLE, account, credentials, user.uid, member, user.language
    )


async def connect_greenhouse(company_id: UUID, body: GreenhouseIn, user: User) -> None:
    """Connects Greenhouse with a Harvest V3 (OAuth) API credential, checked with one read
    first. Each connection gets its own secret key for the web hook the company sets up; a
    reconnect keeps it, so the web hook goes on working."""
    integrations.require_available()
    await integrations.count_connect(company_id, user.uid)
    calling_company.set(company_id)
    client_id, client_secret = body.client_id.strip(), body.client_secret.strip()

    try:
        await greenhouse.check(client_id, client_secret)
    except KeyRejected:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Greenhouse didn't accept this client ID and secret",
        ) from None

    if not await greenhouse.can_write(client_id, client_secret):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, GREENHOUSE_CANT_WRITE)

    kept = await kept_secret(company_id, AtsProvider.GREENHOUSE)
    sealed = integrations.seal(
        {
            "client_id": client_id,
            "client_secret": client_secret,
            "webhook_secret": kept or secrets.token_urlsafe(32),
        }
    )
    # Greenhouse names no account: the page shows the company it's connected for instead.
    await connections.save(
        company_id, AtsProvider.GREENHOUSE, "", sealed, user.uid, language=user.language
    )


async def connect_teamtailor(company_id: UUID, body: TeamtailorIn, user: User) -> None:
    """Connects Teamtailor with an Admin, Read/Write API key, checked first in each region until
    one accepts it. The web hook's signature key comes later (Teamtailor makes it); a reconnect
    keeps it."""
    integrations.require_available()
    await integrations.count_connect(company_id, user.uid)
    calling_company.set(company_id)
    key = body.key.strip()

    try:
        host, company = await teamtailor.region(key)
        await teamtailor.check(host, key)
    except KeyRejected:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Teamtailor didn't accept this key: it needs Admin and Read/Write",
        ) from None

    credentials = {"host": host, "key": key}
    kept = await kept_secret(company_id, AtsProvider.TEAMTAILOR)

    if kept:
        credentials["webhook_secret"] = kept

    # Who results are written back as: the connecting user's Teamtailor user, or an admin.
    member = await teamtailor.member_id(host, key, verified_email(user))
    sealed = integrations.seal(credentials)
    await connections.save(
        company_id, AtsProvider.TEAMTAILOR, company, sealed, user.uid, member, user.language
    )


async def connect_recruitee(company_id: UUID, body: RecruiteeIn, user: User) -> None:
    """Connects Recruitee with the company's address and a personal API token (it acts as the
    person who made it), checked with one read first. The web hook's secret comes later
    (Recruitee shows it); a reconnect keeps it."""
    integrations.require_available()
    account = subdomain(body.account, RECRUITEE_DOMAIN)

    if account is None:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Enter your Recruitee address, like acme.recruitee.com",
        )

    # Counted once the address could be right: a mistyped one is refused before.
    await integrations.count_connect(company_id, user.uid)
    calling_company.set(company_id)

    token = body.token.strip()

    try:
        await recruitee.check(account, token)
    except KeyRejected:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Recruitee didn't accept this token for that company",
        ) from None

    credentials = {"company": account, "token": token}
    kept = await kept_secret(company_id, AtsProvider.RECRUITEE)

    if kept:
        credentials["webhook_secret"] = kept

    sealed = integrations.seal(credentials)
    await connections.save(
        company_id, AtsProvider.RECRUITEE, account, sealed, user.uid, language=user.language
    )


async def breezy_company(token: str) -> dict:
    """The Breezy HR company of the key's person, once the key reads it."""
    try:
        found = await breezy.company(token)

        if found is not None:
            await breezy.check(found["id"], token)
    except KeyRejected:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "Breezy HR didn't accept this key"
        ) from None

    if found is None:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "This key's person has no Breezy HR company"
        )

    return found


async def undo_breezy(company_id: UUID, earlier: AtsConnection | None, user_id: str) -> None:
    """Without its web hook no candidate would come: a new connection doesn't stay (disconnected
    as the member's, so the action log shows it didn't). An earlier one gets its key back, with
    its linked jobs and candidates, marked for reconnecting, as its own web hook may be gone
    already."""
    async with Session.begin() as session:
        if earlier is None:
            await ats.disconnect(session, company_id, AtsProvider.BREEZY, user_id)
        else:
            await ats.restore_broken(session, earlier)

    await outbox_service.flush_quietly()


async def connect_breezy(company_id: UUID, body: BreezyIn, user: User) -> None:
    """Connects Breezy HR with a personal API key (it acts as the person who made it), checked
    with one read first, then creates the web hook that sends its stage changes, whose secret
    Breezy gives only now. A reconnect replaces the earlier web hook; one that fails keeps the
    earlier connection, marked for reconnecting."""
    integrations.require_available()
    await integrations.count_connect(company_id, user.uid)
    calling_company.set(company_id)
    token = body.token.strip()
    found = await breezy_company(token)

    async with Session() as session:
        earlier = await ats.connection(session, company_id, AtsProvider.BREEZY)

    if earlier is not None:
        await integrations.remove_webhook(earlier)

    credentials = {"company": found["id"], "token": token}
    sealed = integrations.seal(credentials)

    async with Session.begin() as session:
        await ats.connect(
            session,
            company_id,
            AtsProvider.BREEZY,
            found["name"],
            sealed,
            user.uid,
            language=user.language,
        )
        connection = await ats.connection(session, company_id, AtsProvider.BREEZY)

    await outbox_service.flush_quietly()
    url = BREEZY_WEBHOOK.format(site=settings.site_url, connection_id=connection.id)

    try:
        hook, secret = await breezy.subscribe(found["id"], token, url)
    except (KeyRejected, HTTPException):
        await undo_breezy(company_id, earlier, user.uid)

        # The account's plan, not the request: a conflict until the company upgrades.
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Breezy HR didn't let us add its web hook: web hooks come with Breezy's Pro plan",
        ) from None

    sealed = integrations.seal({**credentials, "webhook_id": hook, "webhook_secret": secret})

    async with Session.begin() as session:
        await ats.set_credentials(session, connection.id, sealed)
