import calendar
from datetime import datetime

from prepza_common.auth.tokens import new_token

from api.constants.api import KEY_BYTES, KEY_PREFIX, KEY_SHOWN
from api.constants.permissions import IMPLIED, Permission


def new_key() -> tuple[str, str, str]:
    """A new key, its first characters (to tell keys apart) and its hash."""
    key, key_hash = new_token(KEY_PREFIX, KEY_BYTES)

    return key, key[:KEY_SHOWN], key_hash


def expired(expires_at: datetime | None, now: datetime) -> bool:
    """Whether a key with this expiry no longer works; one without never expires."""
    return expires_at is not None and expires_at <= now


def add_months(moment: datetime, months: int) -> datetime:
    """The same day and time `months` later; a day the month doesn't have (Jan 31 + 1) becomes
    its last day."""
    month = moment.month - 1 + months
    year, month = moment.year + month // 12, month % 12 + 1

    return moment.replace(
        year=year, month=month, day=min(moment.day, calendar.monthrange(year, month)[1])
    )


def with_implied(permissions: list[Permission]) -> list[Permission]:
    """The permissions with the reads they imply (IMPLIED), each once, in Permission's order."""
    chosen = set(permissions) | {IMPLIED[item] for item in permissions if item in IMPLIED}

    return [item for item in Permission if item in chosen]
