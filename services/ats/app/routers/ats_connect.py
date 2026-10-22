import json
import secrets
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from prepza_common.auth import CurrentUser
from prepza_common.encryption import decrypt

from app.config.settings import settings
from app.constants.ats import (
    BREEZY_WEBHOOK,
    GREENHOUSE_CANT_WRITE,
    PASTED_KEYS,
    RECRUITEE_DOMAIN,
    WEBHOOKS,
    AtsProvider,
)
from app.helpers.ats import subdomain, verified_email
from app.integrations import breezy, companies, greenhouse, recruitee, teamtailor, workable
from app.integrations.ats_http import calling_company
from app.integrations.errors import KeyRejected
from app.schemas.ats import (
    BreezyIn,
    GreenhouseIn,
    RecruiteeIn,
    TeamtailorIn,
    WebhookKeyIn,
    WebhookOut,
    WorkableIn,
)
from app.services import ats as integrations
from app.services import outbox as outbox_service
from app.storage import ats

# Connecting each ATS, and the web hooks companies set up themselves (Greenhouse, Teamtailor,
# Recruitee).
router = APIRouter(tags=["ats"])


async def kept_secret(company_id: UUID, provider: AtsProvider) -> str | None:
    """The web hook secret key of the connection a reconnect replaces, so its web hook goes on
    working. None when there's none, or its key can't be read any more (the encryption key
    changed): the reconnect then starts afresh."""
    earlier = await ats.connection(company_id, provider)
    opened = decrypt(settings.ats_encryption_key, earlier.credentials) if earlier else None

    return json.loads(opened).get("webhook_secret") if opened else None


@router.put("/workable", status_code=status.HTTP_204_NO_CONTENT)
async def connect_workable(company_id: UUID, body: WorkableIn, user: CurrentUser) -> None:
    """Connects Workable with an account's API access token, checked with one read first. A
    second connect replaces the key."""
    await companies.require(company_id, user.uid, editor=True)
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
    await ats.connect(
        company_id, AtsProvider.WORKABLE, account, credentials, user.uid, member, user.language
    )
    await outbox_service.flush_quietly()


@router.put("/greenhouse", status_code=status.HTTP_204_NO_CONTENT)
async def connect_greenhouse(company_id: UUID, body: GreenhouseIn, user: CurrentUser) -> None:
    """Connects Greenhouse with a Harvest V3 (OAuth) API credential, checked with one read
    first. Each connection gets its own secret key for the web hook the company sets up; a
    reconnect keeps it, so the web hook goes on working."""
    await companies.require(company_id, user.uid, editor=True)
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
    await ats.connect(
        company_id, AtsProvider.GREENHOUSE, "", sealed, user.uid, language=user.language
    )
    await outbox_service.flush_quietly()


@router.put("/teamtailor", status_code=status.HTTP_204_NO_CONTENT)
async def connect_teamtailor(company_id: UUID, body: TeamtailorIn, user: CurrentUser) -> None:
    """Connects Teamtailor with an Admin, Read/Write API key, checked first in each region until
    one accepts it. The web hook's signature key comes later (Teamtailor makes it); a reconnect
    keeps it."""
    await companies.require(company_id, user.uid, editor=True)
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
    await ats.connect(
        company_id, AtsProvider.TEAMTAILOR, company, sealed, user.uid, member, user.language
    )
    await outbox_service.flush_quietly()


@router.put("/recruitee", status_code=status.HTTP_204_NO_CONTENT)
async def connect_recruitee(company_id: UUID, body: RecruiteeIn, user: CurrentUser) -> None:
    """Connects Recruitee with the company's address and a personal API token (it acts as the
    person who made it), checked with one read first. The web hook's secret comes later
    (Recruitee shows it); a reconnect keeps it."""
    await companies.require(company_id, user.uid, editor=True)
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
    await ats.connect(
        company_id, AtsProvider.RECRUITEE, account, sealed, user.uid, language=user.language
    )
    await outbox_service.flush_quietly()


@router.put("/breezy", status_code=status.HTTP_204_NO_CONTENT)
async def connect_breezy(company_id: UUID, body: BreezyIn, user: CurrentUser) -> None:
    """Connects Breezy HR with a personal API key (it acts as the person who made it), checked
    with one read first, then creates the web hook that sends its stage changes, whose secret
    Breezy gives only now. A reconnect replaces the earlier web hook; one that fails keeps the
    earlier connection, marked for reconnecting."""
    await companies.require(company_id, user.uid, editor=True)
    integrations.require_available()
    await integrations.count_connect(company_id, user.uid)
    calling_company.set(company_id)
    token = body.token.strip()

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

    earlier = await ats.connection(company_id, AtsProvider.BREEZY)

    if earlier is not None:
        await integrations.remove_webhook(earlier)

    credentials = {"company": found["id"], "token": token}
    sealed = integrations.seal(credentials)
    await ats.connect(
        company_id, AtsProvider.BREEZY, found["name"], sealed, user.uid, language=user.language
    )
    await outbox_service.flush_quietly()
    connection = await ats.connection(company_id, AtsProvider.BREEZY)
    url = BREEZY_WEBHOOK.format(site=settings.site_url, connection_id=connection.id)

    try:
        hook, secret = await breezy.subscribe(found["id"], token, url)
    except (KeyRejected, HTTPException):
        # Without its web hook no candidate would come: a new connection doesn't stay. An
        # earlier one gets its key back, with its linked jobs and candidates, marked for
        # reconnecting, as its own web hook may be gone already.
        # Disconnected as the member's, so the action log shows the connection didn't stay.
        if earlier is None:
            await ats.disconnect(company_id, AtsProvider.BREEZY, user.uid)
            await outbox_service.flush_quietly()
        else:
            await ats.restore_broken(earlier)

        # The account's plan, not the request: a conflict until the company upgrades.
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Breezy HR didn't let us add its web hook: web hooks come with Breezy's Pro plan",
        ) from None

    sealed = integrations.seal({**credentials, "webhook_id": hook, "webhook_secret": secret})
    await ats.set_credentials(connection.id, sealed)


@router.get("/{provider}/webhook")
async def webhook(company_id: UUID, provider: AtsProvider, user: CurrentUser) -> WebhookOut:
    """Where the company's web hook sends its events, and its secret key (empty while one the
    ATS makes isn't saved yet); owners and admins only."""
    await companies.require(company_id, user.uid, editor=True)

    if provider not in WEBHOOKS:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No web hook to set up")

    connection = await integrations.connected(company_id, provider)
    found = await integrations.credentials(connection)
    url = WEBHOOKS[provider].format(site=settings.site_url, connection_id=connection.id)

    return WebhookOut(url=url, secret=found.get("webhook_secret", ""))


@router.put("/{provider}/webhook", status_code=status.HTTP_204_NO_CONTENT)
async def save_webhook_key(
    company_id: UUID, provider: AtsProvider, body: WebhookKeyIn, user: CurrentUser
) -> None:
    """Saves the secret key the ATS made for the company's web hook (Teamtailor, Recruitee): its
    events count from then on."""
    await companies.require(company_id, user.uid, editor=True)

    if provider not in PASTED_KEYS:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No web hook key to save")

    connection = await integrations.connected(company_id, provider)
    found = await integrations.credentials(connection)
    sealed = integrations.seal({**found, "webhook_secret": body.secret.strip()})
    await ats.set_credentials(connection.id, sealed)
