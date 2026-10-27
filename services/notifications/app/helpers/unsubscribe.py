import base64
import binascii
import hashlib
import hmac
import json

from prepza_common.auth.person_hash import keyed, person_hash
from prepza_common.auth.tokens import same_secret

from app.config.settings import settings
from app.constants.unsubscribe import (
    CANDIDATE_FIELDS,
    ONE_CLICK_BODY,
    ONE_CLICK_PATH,
    PAGE_PATH,
    TOKEN_PURPOSE,
    USER_SETTINGS,
    UnsubscribeType,
)


def encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def decode(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def signature(body: str, secret: str) -> str:
    return encode(hmac.new(secret.encode(), TOKEN_PURPOSE + body.encode(), hashlib.sha256).digest())


def sign(payload: dict, secret: str) -> str:
    """An unsubscribe token: the payload (its "type" and whom it names), then its HMAC-SHA256.
    It never expires: an old email's link keeps working."""
    body = encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode())

    return f"{body}.{signature(body, secret)}"


def user_token(user_id: str, kind: UnsubscribeType, secret: str) -> str:
    return sign({"type": kind, "user_id": user_id}, secret)


def address_hash(email: str) -> str:
    """A candidate's address as links, opt-outs and suppressions name it: a keyed hash, never the
    address itself, nor a plain hash anyone with the address could make."""
    return person_hash(email.strip().lower(), settings.person_hash_key)


def token_address(payload: dict) -> str:
    """The address a candidate's checked token names, as opt-outs keep it. Links in emails sent
    before the hashes were keyed carry the plain SHA-256; it's keyed the same way here."""
    if payload.get("keyed"):
        return payload["address"]

    return keyed(payload["address"], settings.person_hash_key)


def candidate_token(data: dict, kind: UnsubscribeType, secret: str) -> str:
    """For a candidate's email (an invite's data): their address and the company, and for the
    reminders' type the invite too."""
    payload = {
        "type": kind,
        "address": address_hash(data["email"]),
        "keyed": True,
        "company_id": data["company_id"],
        "company": data["company"],
    }

    if kind == UnsubscribeType.INVITE_REMINDERS:
        payload["invite_id"] = data["invite_id"]

    return sign(payload, secret)


def verify(token: str, secret: str) -> dict | None:
    """The token's payload when prepza signed it and it names everything its type needs."""
    body, _, received = token.partition(".")

    if not same_secret(signature(body, secret), received):
        return None

    try:
        payload = json.loads(decode(body))
    except (binascii.Error, ValueError):
        return None

    kind = payload.get("type") if isinstance(payload, dict) else None

    if kind in USER_SETTINGS:
        fields = ("user_id",)
    elif kind in CANDIDATE_FIELDS:
        fields = CANDIDATE_FIELDS[kind]
    else:
        return None

    if not all(isinstance(payload.get(field), str) and payload[field] for field in fields):
        return None

    return payload


def page_url(site_url: str, token: str) -> str:
    return site_url.rstrip("/") + PAGE_PATH.format(token=token)


def one_click_headers(site_url: str, token: str) -> dict[str, str]:
    """Mail clients' own unsubscribe button: a POST to this address unsubscribes at once."""
    url = site_url.rstrip("/") + ONE_CLICK_PATH.format(token=token)

    return {"List-Unsubscribe": f"<{url}>", "List-Unsubscribe-Post": ONE_CLICK_BODY}
