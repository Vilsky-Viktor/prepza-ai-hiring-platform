import hashlib
import hmac

from testee_common.auth.tokens import same_secret


def signature_valid(header: str, body: bytes, secret: str, now: float, tolerance: int) -> bool:
    """Checks Paddle's `Paddle-Signature: ts=...;h1=...`: an HMAC-SHA256 of "ts:body" with the
    webhook secret, made within `tolerance` seconds. While Paddle rotates the secret it sends
    an h1 for each; one matching is enough."""
    if not secret:
        return False

    parts = [part.split("=", 1) for part in header.split(";") if "=" in part]
    timestamp = next((value for name, value in parts if name == "ts"), "")
    received = [value for name, value in parts if name == "h1"]

    if not timestamp.isdigit() or abs(now - int(timestamp)) > tolerance:
        return False

    expected = hmac.new(
        secret.encode(), f"{timestamp}:".encode() + body, hashlib.sha256
    ).hexdigest()

    return any(same_secret(expected, value) for value in received)
