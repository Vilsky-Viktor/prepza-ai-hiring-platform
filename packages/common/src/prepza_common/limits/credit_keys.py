"""One-off migrations of the keys of candidates' credits: companies (an invite's hold_key) and
billing (its holds and entries) rewrite their own copies of a key, and must arrive at the same
new one. Both get it here. The first took the email out of the keys, as a plain hash; the second
keys that hash, as anyone with the email and the interview could match it."""

from prepza_common.auth.person_hash import keyed

# The hex digits of a key's hash, as the first migration left them.
KEY_HASH_LENGTH = 32


def hashed(old: str) -> str:
    """The first 32 hex digits of the SHA-256 of `old`, an SQL text expression."""
    return f"left(encode(sha256(convert_to({old}, 'UTF8')), 'hex'), 32)"


def invite_key(interview_id: str, old: str) -> str:
    """Companies' new key for an invite: "{interview_id}:{hash of the old key}"."""
    return f"{interview_id}::text || ':' || {hashed(old)}"


def ledger_key(key: str) -> str:
    """Billing's new key for a "candidate:{interview_id}:{email}[:{uuid}]" hold or entry: the
    same as companies', after "candidate:"."""
    old = f"substr({key}, 11)"

    return f"'candidate:' || split_part({old}, ':', 1) || ':' || {hashed(old)}"


def rekeyed(hold_key: str, secret: str) -> str:
    """An invite's hold key "{interview_id}:{hash}" with its hash keyed (PERSON_HASH_KEY): what
    both services' second migration makes of every candidate's key."""
    interview_id, _, rest = hold_key.partition(":")

    return f"{interview_id}:{keyed(rest, secret)[:KEY_HASH_LENGTH]}"
