import logging
import secrets
import time
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, status
from prepza_common.encryption import decrypt, encrypt
from prepza_common.notifications import NotificationKind, Recipient, notification
from prepza_common.tokens import purpose_key

from app.config.settings import settings
from app.constants.slack import (
    SLACK_AUTHORIZE_URL,
    SLACK_CALLBACK,
    SLACK_DEFAULT_KINDS,
    SLACK_KINDS,
    SLACK_LINK,
    SLACK_PAGE,
    SLACK_SCOPE,
    SLACK_STATE_KEY,
    SLACK_STATE_PURPOSE,
    SLACK_STATE_SECONDS,
)
from app.helpers.slack import message, read_state, signed_state
from app.integrations import companies, slack
from app.integrations.redis import get_redis
from app.schemas.slack import SlackOut
from app.services import outbox as outbox_service
from app.services.feed import announce
from app.storage import notifications
from app.storage import slack as storage

logger = logging.getLogger(__name__)


def available() -> bool:
    return bool(
        settings.slack_client_id and settings.slack_client_secret and settings.slack_encryption_key
    )


async def overview(company_id: str) -> SlackOut:
    found = await storage.get(company_id)
    kinds = [str(kind) for kind in SLACK_KINDS]

    if found is None:
        return SlackOut(connected=False, kinds=[], all_kinds=kinds)

    return SlackOut(
        connected=True,
        status=found.status,
        team=found.team,
        channel=found.channel,
        kinds=found.kinds,
        all_kinds=kinds,
    )


def state_key() -> str:
    """Signs the "Add to Slack" trip's state: a key of its own, made from the service's."""
    return purpose_key(settings.service_secret, SLACK_STATE_PURPOSE)


async def start(company_id: str, user_id: str) -> str:
    """Slack's approval page, for the company's editor who pressed "Add to Slack"."""
    if not available():
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Slack isn't set up yet")

    nonce = secrets.token_urlsafe(16)
    await get_redis().set(SLACK_STATE_KEY.format(nonce=nonce), 1, ex=SLACK_STATE_SECONDS)
    expires = int(time.time()) + SLACK_STATE_SECONDS
    state = signed_state(state_key(), company_id, user_id, expires, nonce)
    query = urlencode(
        {
            "client_id": settings.slack_client_id,
            "scope": SLACK_SCOPE,
            "redirect_uri": SLACK_CALLBACK.format(site=settings.site_url),
            "state": state,
        }
    )

    return f"{SLACK_AUTHORIZE_URL}?{query}"


async def finish(code: str | None, state: str, error: str | None) -> str:
    """Back from Slack: the approved channel is saved (replacing an earlier one, whose app is
    removed unless a company still uses it). Each state works once, and only while whoever
    started the trip is still an editor. Where to send the browser: the company's Slack page,
    saying how it went."""
    found = read_state(state_key(), state, int(time.time()))

    # Deleting the nonce takes the state: a second callback with it finds nothing.
    if found is None or not await get_redis().delete(SLACK_STATE_KEY.format(nonce=found[2])):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This Slack link expired: try again")

    company_id, user_id, _ = found
    await companies.require(company_id, user_id, editor=True)
    page = SLACK_PAGE.format(site=settings.site_url, company_id=company_id)

    if error or not code:
        return f"{page}?slack=cancelled"

    try:
        hook = await slack.exchange(code)
    except (slack.SlackRefused, httpx.HTTPError):
        logger.exception("Couldn't finish connecting Slack for %s", company_id)

        return f"{page}?slack=failed"

    earlier = await storage.get(company_id)
    key = settings.slack_encryption_key
    await storage.connect(
        company_id,
        hook["team"],
        hook["channel"],
        encrypt(key, hook["url"]),
        encrypt(key, hook["token"]),
        earlier.kinds if earlier else [str(kind) for kind in SLACK_DEFAULT_KINDS],
        user_id,
    )

    await outbox_service.flush_quietly()

    if earlier is not None:
        await remove_app(earlier.token)

    return f"{page}?slack=connected"


async def set_kinds(company_id: str, kinds: list[str], user_id: str) -> None:
    if await storage.get(company_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Slack isn't connected")

    chosen = [kind for kind in map(str, SLACK_KINDS) if kind in kinds]
    await storage.set_kinds(company_id, chosen, user_id)
    await outbox_service.flush_quietly()


async def remove_app(sealed_token: str) -> None:
    """Revokes a token no company uses any more. Slack gives every company on a workspace (and a
    company reconnecting to it) the same token, and revoking it removes the app for all of them."""
    key = settings.slack_encryption_key
    token = decrypt(key, sealed_token)

    if token and token not in [decrypt(key, sealed) for sealed in await storage.tokens()]:
        await slack.revoke(token)


async def disconnect(company_id: str, user_id: str | None = None) -> None:
    """Removes the channel, then prepza's app from the workspace (as far as Slack answers) unless
    another company still uses it. A member's (`user_id`) goes to the company's action log."""
    found = await storage.get(company_id)

    if found is not None:
        await storage.remove(company_id, user_id)
        await outbox_service.flush_quietly()
        await remove_app(found.token)


async def deliver(event: dict, key: str) -> None:
    """A company's notification goes to its Slack channel too, if it chose that kind and whoever
    connected it is still an owner or admin; once per `key` (the bell's), however often its event
    comes. Every one is posted, also one the bell groups with others ("3 candidates finished"). A
    gone web hook, or a connector no longer an editor, marks the channel for
    reconnecting, and a message Slack refuses is logged: neither is retried. Slack (or the
    companies service) busy or down raises, so Pub/Sub retries the event, backing off, and the
    retry posts it."""
    if event.get("recipient") != Recipient.COMPANY or not available():
        return

    company_id = event["recipient_id"]
    found = await storage.connected(company_id)
    text = message(event, settings.site_url)

    if found is None or event.get("kind") not in found.kinds or text is None:
        return

    # The channel works while whoever connected it is still an owner or admin, like an API key;
    # otherwise an editor reconnects it.
    if not (await companies.access(company_id, found.created_by))["editor"]:
        await stop(company_id)

        return

    webhook = decrypt(settings.slack_encryption_key, found.webhook)

    if webhook is None:
        await stop(company_id)

        return

    # Claimed before posting, so two deliveries of one event at once post it once.
    if not await storage.claim(key):
        return

    try:
        await slack.post(webhook, text)
    except slack.WebhookGone:
        await stop(company_id)
    except slack.SlackRefused as refused:
        logger.warning(
            "Slack refused a %s notification for %s: %s", event["kind"], company_id, refused.error
        )
    except Exception:
        await storage.release(key)

        raise


async def stop(company_id: str) -> None:
    """Marks the company's channel for reconnecting; told once when it stops working."""
    if await storage.mark_broken(company_id):
        await stopped(company_id)


async def stopped(company_id: str) -> None:
    """Tells the company its channel stopped working: in the bell, not in Slack, which is what
    broke. A lost notification is better than a failed delivery."""
    data = notification(
        Recipient.COMPANY,
        company_id,
        NotificationKind.CONNECTION_BROKEN,
        SLACK_LINK.format(company_id=company_id),
        name="Slack",
        integration="slack",
    )

    try:
        await notifications.add(f"connection_broken:{secrets.token_hex(16)}", data)
        await announce(Recipient.COMPANY, company_id)
    except Exception:
        logger.exception("Couldn't tell company %s its Slack channel stopped working", company_id)
