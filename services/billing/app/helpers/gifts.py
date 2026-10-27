from prepza_common.auth.person_hash import person_hash

from app.constants.gifts import DOTLESS_DOMAINS, GMAIL


def inbox_of(email: str) -> str:
    """The inbox an address delivers to: case, a "+tag" and Gmail's dots don't make another
    person, so they can't claim a welcome gift twice."""
    local, _, domain = email.strip().lower().rpartition("@")
    local = local.split("+", 1)[0]

    if domain in DOTLESS_DOMAINS:
        local = local.replace(".", "")
        domain = GMAIL

    return f"{local}@{domain}"


def legacy_gift_key(kind: str, email: str, key: str) -> str:
    """The key gifts had before inbox_of: the lowercased email. Still checked, so an owner who
    got a gift then can't get it again under the new key."""
    return f"{kind}:{person_hash(email.strip().lower(), key)}"


def gift_key(kind: str, email: str, key: str) -> str:
    """Names a welcome gift by a keyed hash of the inbox (`key`, PERSON_HASH_KEY): it can be
    matched again, never read back, nor matched by anyone with a list of addresses."""
    return f"{kind}:{person_hash(inbox_of(email), key)}"
