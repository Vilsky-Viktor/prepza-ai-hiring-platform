import socket
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from prepza_common.auth.encryption import encrypt
from prepza_common.http.public_urls import resolved_address
from prepza_common.i18n.i18n import TemplateError
from prepza_common.limits.limits import limit, record_hit
from prepza_common.limits.rate_limit import hit_or_skip

from api.config import settings
from api.constants.api import KEY_EXPIRY_MONTHS, SECRET_OVERLAP, KeyExpiry
from api.constants.permissions import (
    DEFAULT_PERMISSIONS,
    IMPLIED,
    PERMISSION_GROUPS,
    Permission,
)
from api.core.db import Session
from api.helpers.keys import add_months, expired, new_key, with_implied
from api.helpers.webhooks import masked, new_secret
from api.integrations import companies
from api.integrations.redis import get_redis
from api.models.api import ApiKey, Webhook
from api.repositories import keys, webhooks
from api.repositories import webhook_log as webhook_log_store
from api.schemas.manage import (
    ApiSettingsOut,
    KeyOut,
    NewKeyOut,
    NewSecretOut,
    NewWebhookOut,
    WebhookAttemptOut,
    WebhookOut,
)
from api.services import webhooks as webhook_events


async def overview(company_id: UUID, editor: bool) -> ApiSettingsOut:
    """A web hook shows as stopped while the member who added it is no longer an owner or admin,
    as it gets no events then (services/webhooks.py). Only an `editor` sees its whole address."""
    async with Session() as session:
        hooks = await webhooks.of_company(session, company_id)
        company_keys = await keys.of_company(session, company_id)

    editors = {
        maker: (await companies.access(company_id, maker))["editor"]
        for maker in {hook.created_by for hook in hooks}
    }

    return ApiSettingsOut(
        keys=[key_out(key) for key in company_keys],
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
        allowed_ips=key.allowed_ips,
    )


async def create_key(
    company_id: UUID,
    name: str,
    expiry: KeyExpiry,
    permissions: list[Permission],
    allowed_ips: list[str],
    user_id: str,
) -> NewKeyOut:
    key, shown, hashed = new_key()
    months = KEY_EXPIRY_MONTHS[expiry]
    expires_at = add_months(datetime.now(UTC), months) if months else None
    most = await limit(get_redis(), "MAX_API_KEYS")

    async with Session.begin() as session:
        row = await keys.add(
            session,
            company_id,
            name.strip(),
            shown,
            hashed,
            user_id,
            expires_at,
            with_implied(permissions),
            allowed_ips,
            most,
        )

    if row is None:
        await record_hit("MAX_API_KEYS", company_id=company_id, user_id=user_id)

        raise TemplateError(
            status.HTTP_409_CONFLICT, "A company can have up to {limit} API keys", limit=most
        )

    return NewKeyOut(**key_out(row).model_dump(), key=key)


async def change_key_permissions(
    company_id: UUID, key_id: UUID, permissions: list[Permission], user_id: str
) -> KeyOut:
    """Replaces the key's permissions, with the reads they imply; the change applies to its next
    call."""
    async with Session.begin() as session:
        row = await keys.change_permissions(
            session, company_id, key_id, with_implied(permissions), user_id
        )

    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "API key not found")

    return key_out(row)


async def set_key_ips(
    company_id: UUID, key_id: UUID, allowed_ips: list[str], user_id: str
) -> KeyOut:
    """Replaces the addresses the key may be used from; the change applies to its next call."""
    async with Session.begin() as session:
        row = await keys.set_allowed_ips(session, company_id, key_id, allowed_ips, user_id)

    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "API key not found")

    return key_out(row)


async def remove_key(company_id: UUID, key_id: UUID, user_id: str) -> None:
    async with Session.begin() as session:
        removed = await keys.remove(session, company_id, key_id, user_id)

    if not removed:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "API key not found")


async def create_webhook(company_id: UUID, url: str, user_id: str) -> NewWebhookOut:
    """A web hook to an HTTPS address on the public internet, with a new signing secret."""
    if not settings.api_encryption_key:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Web hooks aren't set up yet")

    url = url.strip()

    try:
        address = await resolved_address(url)
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

    async with Session.begin() as session:
        row = await webhooks.add(session, company_id, url, sealed, user_id, most)

    if row is None:
        await record_hit("MAX_WEBHOOKS", company_id=company_id, user_id=user_id)

        raise TemplateError(
            status.HTTP_409_CONFLICT, "A company can have up to {limit} web hooks", limit=most
        )

    return NewWebhookOut(
        **WebhookOut.model_validate(row, from_attributes=True).model_dump(), secret=secret
    )


async def rotate_secret(company_id: UUID, webhook_id: UUID, user_id: str) -> NewSecretOut:
    """A new signing secret for the web hook, shown once; the old one signs too for
    SECRET_OVERLAP, so the receiver switches over without missing an event."""
    secret = new_secret()
    until = datetime.now(UTC) + SECRET_OVERLAP
    sealed = encrypt(settings.api_encryption_key, secret)

    async with Session.begin() as session:
        rotated = await webhooks.rotate(session, company_id, webhook_id, sealed, until, user_id)

    if rotated is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Web hook not found")

    return NewSecretOut(secret=secret, previous_until=until)


async def remove_webhook(company_id: UUID, webhook_id: UUID, user_id: str) -> None:
    async with Session.begin() as session:
        removed = await webhooks.remove(session, company_id, webhook_id, user_id)

    if not removed:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Web hook not found")


async def webhook(company_id: UUID, webhook_id: UUID) -> Webhook:
    async with Session() as session:
        found = await webhooks.get(session, company_id, webhook_id)

    if found is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Web hook not found")

    return found


async def webhook_log(company_id: UUID, webhook_id: UUID) -> list[WebhookAttemptOut]:
    hook = await webhook(company_id, webhook_id)

    async with Session() as session:
        rows = await webhook_log_store.latest(session, hook.id)

    return [WebhookAttemptOut.model_validate(row, from_attributes=True) for row in rows]


async def test_webhook(company_id: UUID, webhook_id: UUID, user_id: str) -> bool:
    """A signed test event sent to the company's web hook now, up to WEBHOOK_TESTS_PER_HOUR a
    company; whether it took it. The company's action log gets it as `user_id`'s."""
    hook = await webhook(company_id, webhook_id)
    await hit_or_skip(
        get_redis(),
        f"rate:webhook-tests:{company_id}",
        "WEBHOOK_TESTS_PER_HOUR",
        company_id=company_id,
        user_id=user_id,
    )
    ok = await webhook_events.test(hook)

    async with Session.begin() as session:
        await webhooks.tested(session, hook, user_id)

    return ok
