import hashlib
import hmac
import secrets


def hashed(token: str) -> str:
    """What's stored of a secret token (an API key, an AI app's access): its SHA-256, so a
    leaked database gives no working tokens."""
    return hashlib.sha256(token.encode()).hexdigest()


def new_token(prefix: str, size: int) -> tuple[str, str]:
    """A new random token, `prefix` and `size` random bytes in URL-safe characters, and its
    hash."""
    token = prefix + secrets.token_urlsafe(size)

    return token, hashed(token)


def same_secret(given: str, expected: str) -> bool:
    """Whether a received signature or token is the expected one, in constant time. Compared as
    bytes: hmac.compare_digest refuses text that isn't ASCII with an error, which anyone could
    send to make a server error."""
    return hmac.compare_digest(given.encode(), expected.encode())


def purpose_key(secret: str, purpose: str) -> str:
    """A key of its own for one use of `secret` (a service's key signing a Slack trip's state or
    the help chat's replies): whoever holds the service key to call the service can't make
    those signatures with it."""
    return hmac.new(secret.encode(), b"purpose:" + purpose.encode(), hashlib.sha256).hexdigest()
