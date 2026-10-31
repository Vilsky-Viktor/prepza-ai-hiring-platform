from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from testee_common.auth.auth import CurrentUser

from ats.config import settings
from ats.constants.ats import PASTED_KEYS, WEBHOOKS, AtsProvider
from ats.integrations import companies
from ats.schemas.ats import (
    BreezyIn,
    GreenhouseIn,
    RecruiteeIn,
    TeamtailorIn,
    WebhookKeyIn,
    WebhookOut,
    WorkableIn,
)
from ats.services import ats as integrations
from ats.services import connect, connections

# Connecting each ATS, and the web hooks companies set up themselves (Greenhouse, Teamtailor,
# Recruitee).
router = APIRouter(tags=["ats"])


@router.put("/workable", status_code=status.HTTP_204_NO_CONTENT)
async def connect_workable(company_id: UUID, body: WorkableIn, user: CurrentUser) -> None:
    """Connects Workable with an account's API access token, checked with one read first. A
    second connect replaces the key."""
    await companies.require(company_id, user.uid, editor=True)
    await connect.connect_workable(company_id, body, user)


@router.put("/greenhouse", status_code=status.HTTP_204_NO_CONTENT)
async def connect_greenhouse(company_id: UUID, body: GreenhouseIn, user: CurrentUser) -> None:
    """Connects Greenhouse with a Harvest V3 (OAuth) API credential, checked with one read
    first. Each connection gets its own secret key for the web hook the company sets up; a
    reconnect keeps it, so the web hook goes on working."""
    await companies.require(company_id, user.uid, editor=True)
    await connect.connect_greenhouse(company_id, body, user)


@router.put("/teamtailor", status_code=status.HTTP_204_NO_CONTENT)
async def connect_teamtailor(company_id: UUID, body: TeamtailorIn, user: CurrentUser) -> None:
    """Connects Teamtailor with an Admin, Read/Write API key, checked first in each region until
    one accepts it. The web hook's signature key comes later (Teamtailor makes it); a reconnect
    keeps it."""
    await companies.require(company_id, user.uid, editor=True)
    await connect.connect_teamtailor(company_id, body, user)


@router.put("/recruitee", status_code=status.HTTP_204_NO_CONTENT)
async def connect_recruitee(company_id: UUID, body: RecruiteeIn, user: CurrentUser) -> None:
    """Connects Recruitee with the company's address and a personal API token (it acts as the
    person who made it), checked with one read first. The web hook's secret comes later
    (Recruitee shows it); a reconnect keeps it."""
    await companies.require(company_id, user.uid, editor=True)
    await connect.connect_recruitee(company_id, body, user)


@router.put("/breezy", status_code=status.HTTP_204_NO_CONTENT)
async def connect_breezy(company_id: UUID, body: BreezyIn, user: CurrentUser) -> None:
    """Connects Breezy HR with a personal API key (it acts as the person who made it), checked
    with one read first, then creates the web hook that sends its stage changes, whose secret
    Breezy gives only now. A reconnect replaces the earlier web hook; one that fails keeps the
    earlier connection, marked for reconnecting."""
    await companies.require(company_id, user.uid, editor=True)
    await connect.connect_breezy(company_id, body, user)


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

    await connections.save_webhook_key(company_id, provider, body.secret.strip())
