import base64
import binascii
import hashlib
import hmac

from prepza_common.auth.tokens import same_secret


def signature_valid(
    message_id: str,
    timestamp: str,
    header: str,
    body: bytes,
    secret: str,
    now: float,
    tolerance: int,
) -> bool:
    """Checks Resend's (Svix) `svix-signature: v1,<base64> ...`: an HMAC-SHA256 of
    "id.timestamp.body" keyed with the base64 part of the `whsec_` secret, made within
    `tolerance` seconds."""
    if not secret or not message_id or not timestamp.isdigit():
        return False

    if abs(now - int(timestamp)) > tolerance:
        return False

    try:
        key = base64.b64decode(secret.removeprefix("whsec_"))
    except binascii.Error:
        return False

    signed = f"{message_id}.{timestamp}.".encode() + body
    expected = base64.b64encode(hmac.new(key, signed, hashlib.sha256).digest()).decode()
    received = [part.split(",", 1)[1] for part in header.split() if part.startswith("v1,")]

    return any(same_secret(expected, signature) for signature in received)
