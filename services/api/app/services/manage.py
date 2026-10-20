import asyncio
import socket
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from prepza_common.encryption import encrypt
from prepza_common.i18n import TemplateError
from prepza_common.limits import limit, record_hit
from prepza_common.public_urls import public_address

from app.config.settings import settings
from app.constants.api import KEY_EXPIRY_MONTHS, KeyExpiry
from app.constants.permissions import (
    DEFAULT_PERMISSIONS,
    IMPLIED,
    ONLY_NARROWING,
    PERMISSION_GROUPS,
    Permission,
)
from app.helpers.keys import add_months, expired, new_key, with_implied
from app.helpers.webhooks import masked, new_secret
from app.integrations import companies
from app.integrations.redis import get_redis
from app.models.api import ApiKey, Webhook
from app.schemas.manage import (
    ApiSettingsOut,
    KeyOut,
    NewKeyOut,
    NewWebhookOut,
    WebhookAttemptOut,
    WebhookOut,
)
from app.storage import keys, webhooks
from app.storage import webhook_log as webhook_log_store


async def overview(company_id: UUID, editor: bool) -> ApiSettingsOut:
    """A web hook shows as stopped while the member who added it is no longer an owner or admin,
    as it gets no events then (services/webhooks.py). Only an `editor` sees its whole address."""
    hooks = await webhooks.of_company(company_id)
    editors = {
        maker: (await companies.access(company_id, maker))["editor"]
        for maker in {hook.created_by for hook in hooks}
    }

    return ApiSettingsOut(
        keys=[key_out(key) for key in await keys.of_company(company_id)],
        webhooks=[
            WebhookOut.model_validate(hook, from_attributes=True).model_copy(
                update={
                    "stopped": not editors[hook.created_by],
                    "url": hook.url if editor else masked(hook.url),
                }
            )
            for hook in hooks
        ],
        expiries=list(KeyExpiry),
        permission_groups=PERMISSION_GROUPS,
        implied=IMPLIED,
        default_permissions=DEFAULT_PERMISSIONS,
    )


def key_out(key: ApiKey) -> KeyOut:
    return KeyOut(
        id=key.id,
        name=key.name,
        shown=key.shown,
        created_at=key.created_at,
        expires_at=key.expires_at,
        expired=expired(key.expires_at, datetime.now(UTC)),
        last_used_at=key.last_used_at,
        permissions=key.permissions,
    )


async def create_key(
    company_id: UUID, name: str, expiry: KeyExpiry, permissions: list[Permission], user_id: str
) -> NewKeyOut:
    key, shown, hashed = new_key()
    months = KEY_EXPIRY_MONTHS[expiry]
    expires_at = add_months(datetime.now(UTC), months) if months else None
    most = await limit(get_redis(), "MAX_API_KEYS")
    row = await keys.add(
        company_id,
        name.strip(),
        shown,
        hashed,
        user_id,
        expires_at,
        with_implied(permissions),
        most,
    )

    if row is None:
        await record_hit("MAX_API_KEYS", company_id=company_id, user_id=user_id)

        raise TemplateError(
            status.HTTP_409_CONFLICT, "A company can have up to {limit} API keys", limit=most
        )

    return NewKeyOut(**key_out(row).model_dump(), key=key)


async def narrow_key(
    company_id: UUID, key_id: UUID, permissions: list[Permission], user_id: str
) -> KeyOut:
    """Only takes permissions away: a leaked key never gains one."""
    row = await keys.narrow(company_id, key_id, with_implied(permissions), user_id)

    if row is None and await keys.get(company_id, key_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "API key not found")

    if row is None:
        raise HTTPException(status.HTTP_409_CONFLICT, ONLY_NARROWING)

    return key_out(row)


async def remove_key(company_id: UUID, key_id: UUID, user_id: str) -> None:
    if not await keys.remove(company_id, key_id, user_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "API key not found")


async def create_webhook(company_id: UUID, url: str, user_id: str) -> NewWebhookOut:
    """A web hook to an HTTPS address on the public internet, with a new signing secret."""
    if not settings.api_encryption_key:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Web hooks aren't set up yet")

    url = url.strip()

    try:
        address = await asyncio.to_thread(public_address, url)
    except socket.gaierror:
        address = None

    if address is None:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Use an HTTPS address that's reachable from the internet",
        )

    secret = new_secret()
    sealed = encrypt(settings.api_encryption_key, secret)
    most = await limit(get_redis(), "MAX_WEBHOOKS")
    row = await webhooks.add(company_id, url, sealed, user_id, most)

    if row is None:
        await record_hit("MAX_WEBHOOKS", company_id=company_id, user_id=user_id)

        raise TemplateError(
            status.HTTP_409_CONFLICT, "A company can have up to {limit} web hooks", limit=most
        )

    return NewWebhookOut(
        **WebhookOut.model_validate(row, from_attributes=True).model_dump(), secret=secret
    )


async def remove_webhook(company_id: UUID, webhook_id: UUID, user_id: str) -> None:
    if not await webhooks.remove(company_id, webhook_id, user_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Web hook not found")


async def webhook(company_id: UUID, webhook_id: UUID) -> Webhook:
    found = await webhooks.get(company_id, webhook_id)

    if found is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Web hook not found")

    return found


async def webhook_log(company_id: UUID, webhook_id: UUID) -> list[WebhookAttemptOut]:
    hook = await webhook(company_id, webhook_id)

    return [
        WebhookAttemptOut.model_validate(row, from_attributes=True)
        for row in await webhook_log_store.latest(hook.id)
    ]
