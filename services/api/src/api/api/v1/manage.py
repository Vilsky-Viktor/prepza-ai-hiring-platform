from uuid import UUID

from fastapi import APIRouter, status
from prepza_common.auth.auth import CurrentUser

from api.integrations import companies
from api.schemas.manage import (
    ApiSettingsOut,
    KeyIn,
    KeyIpsIn,
    KeyOut,
    KeyPermissionsIn,
    NewKeyOut,
    NewSecretOut,
    NewWebhookOut,
    WebhookAttemptOut,
    WebhookIn,
    WebhookTestOut,
)
from api.services import manage
from api.services import outbox as outbox_service

# The company's keys and web hooks, for its API page; not part of the public API.
router = APIRouter(prefix="/manage", tags=["manage"], include_in_schema=False)


@router.get("")
async def get_settings(company_id: UUID, user: CurrentUser) -> ApiSettingsOut:
    """Every member sees the keys (never the keys themselves) and web hooks; only owners and
    admins their whole addresses."""
    found = await companies.require(company_id, user.uid)

    return await manage.overview(company_id, found["editor"])


@router.post("/keys", status_code=status.HTTP_201_CREATED)
async def create_key(company_id: UUID, body: KeyIn, user: CurrentUser) -> NewKeyOut:
    await companies.require(company_id, user.uid, editor=True)

    created = await manage.create_key(
        company_id, body.name, body.expiry, body.permissions, body.allowed_ips, user.uid
    )
    await outbox_service.flush_quietly()

    return created


@router.patch("/keys/{key_id}")
async def change_key_permissions(
    company_id: UUID, key_id: UUID, body: KeyPermissionsIn, user: CurrentUser
) -> KeyOut:
    """Owners and admins replace a key's permissions, adding or taking away any."""
    await companies.require(company_id, user.uid, editor=True)

    changed = await manage.change_key_permissions(company_id, key_id, body.permissions, user.uid)
    await outbox_service.flush_quietly()

    return changed


@router.put("/keys/{key_id}/allowed-ips")
async def set_key_ips(company_id: UUID, key_id: UUID, body: KeyIpsIn, user: CurrentUser) -> KeyOut:
    """Owners and admins limit a key to the addresses its servers call from, or let it be used
    from any (an empty list)."""
    await companies.require(company_id, user.uid, editor=True)

    changed = await manage.set_key_ips(company_id, key_id, body.allowed_ips, user.uid)
    await outbox_service.flush_quietly()

    return changed


@router.delete("/keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_key(company_id: UUID, key_id: UUID, user: CurrentUser) -> None:
    await companies.require(company_id, user.uid, editor=True)
    await manage.remove_key(company_id, key_id, user.uid)
    await outbox_service.flush_quietly()


@router.post("/webhooks", status_code=status.HTTP_201_CREATED)
async def create_webhook(company_id: UUID, body: WebhookIn, user: CurrentUser) -> NewWebhookOut:
    await companies.require(company_id, user.uid, editor=True)

    created = await manage.create_webhook(company_id, body.url, user.uid)
    await outbox_service.flush_quietly()

    return created


@router.delete("/webhooks/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_webhook(company_id: UUID, webhook_id: UUID, user: CurrentUser) -> None:
    await companies.require(company_id, user.uid, editor=True)
    await manage.remove_webhook(company_id, webhook_id, user.uid)
    await outbox_service.flush_quietly()


@router.post("/webhooks/{webhook_id}/secret")
async def rotate_secret(company_id: UUID, webhook_id: UUID, user: CurrentUser) -> NewSecretOut:
    """Owners and admins give a web hook a new signing secret, shown once; the old one keeps
    signing too for a day, so its receiver can switch over."""
    await companies.require(company_id, user.uid, editor=True)

    rotated = await manage.rotate_secret(company_id, webhook_id, user.uid)
    await outbox_service.flush_quietly()

    return rotated


@router.post("/webhooks/{webhook_id}/test")
async def test_webhook(company_id: UUID, webhook_id: UUID, user: CurrentUser) -> WebhookTestOut:
    """Owners and admins send a signed test event to a web hook, now."""
    await companies.require(company_id, user.uid, editor=True)

    ok = await manage.test_webhook(company_id, webhook_id, user.uid)
    await outbox_service.flush_quietly()

    return WebhookTestOut(ok=ok)


@router.get("/webhooks/{webhook_id}/log")
async def webhook_log(
    company_id: UUID, webhook_id: UUID, user: CurrentUser
) -> list[WebhookAttemptOut]:
    """A web hook's latest sends and how they went, newest first; every member sees them."""
    await companies.require(company_id, user.uid)

    return await manage.webhook_log(company_id, webhook_id)
