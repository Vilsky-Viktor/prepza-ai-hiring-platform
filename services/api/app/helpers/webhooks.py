import hashlib
import hmac
import json
import random
import secrets
from datetime import datetime, timedelta
from urllib.parse import urlsplit

from app.constants.api import RETRY_FIRST_DELAY, RETRY_MAX_DELAY


def new_secret() -> str:
    """A web hook's signing secret, shown once."""
    return "whsec_" + secrets.token_urlsafe(30)


def masked(url: str) -> str:
    """A web hook's address as members who can't change it see it: its site only, as the rest
    (a Zapier or Make path, say) works like a password."""
    parts = urlsplit(url)
    port = f":{parts.port}" if parts.port else ""

    return f"{parts.scheme}://{parts.hostname}{port}/…"


def body_of(event_id: str, event_type: str, data: dict, occurred_at: datetime) -> bytes:
    """What a web hook gets: the event's id (the same on a repeat), its type, when the change
    happened (to put events in order: a retried event can arrive after a later one) and data."""
    event = {
        "id": event_id,
        "type": event_type,
        "occurred_at": occurred_at.isoformat(),
        "data": data,
    }

    return json.dumps(event, separators=(",", ":")).encode()


def signature(secret: str, timestamp: int, body: bytes) -> str:
    """The signature header: HMAC-SHA256 of "<timestamp>.<body>" with the web hook's secret."""
    digest = hmac.new(secret.encode(), f"{timestamp}.".encode() + body, hashlib.sha256)

    return f"t={timestamp},v1={digest.hexdigest()}"


def retry_delay(attempts: int, share: float | None = None) -> timedelta:
    """How long an event waits to be sent again after its `attempts`-th failed send: up to twice
    as long each time, from RETRY_FIRST_DELAY up to RETRY_MAX_DELAY, less a random share of up
    to half (equal jitter), so events that failed together, when an endpoint was down, don't all
    come back together. `share` (0 to 1) fixes the random part."""
    longest = min(RETRY_FIRST_DELAY * 2 ** (attempts - 1), RETRY_MAX_DELAY)
    share = random.random() if share is None else share

    return max(longest * (1 - share / 2), RETRY_FIRST_DELAY)
