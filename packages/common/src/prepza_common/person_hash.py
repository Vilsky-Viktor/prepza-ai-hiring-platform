"""Hashes that stand for a person (an email address): keyed, so only whoever holds the key
(PERSON_HASH_KEY, in Secret Manager) can match an address to one, never anyone with a list of
addresses. The key is kept apart from the rows that hold the hashes."""

import hashlib
import hmac


def digest(text: str) -> str:
    """The plain SHA-256 of `text`: what older rows and links held, never stored on its own."""
    return hashlib.sha256(text.encode()).hexdigest()


def keyed(plain_digest: str, key: str) -> str:
    """The keyed hash of a plain digest: how rows that held the digest are moved to keyed ones,
    and the last step of `person_hash`."""
    return hmac.new(key.encode(), plain_digest.encode(), hashlib.sha256).hexdigest()


def person_hash(text: str, key: str) -> str:
    """The keyed hash that stands for `text` (an email address, normalised by the caller)."""
    return keyed(digest(text), key)
