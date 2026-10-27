import time

# Values kept in this process's memory (one service instance) for a while, by key, with when
# each expires.
_entries: dict[str, tuple[float, object]] = {}


def get(key: str) -> object | None:
    found = _entries.get(key)

    if found is None or found[0] < time.monotonic():
        return None

    return found[1]


def put(key: str, value: object, seconds: int) -> None:
    now = time.monotonic()

    # Expired values go, so keys that aren't asked for again don't pile up.
    for old in [name for name, (expires, _) in _entries.items() if expires < now]:
        del _entries[old]

    _entries[key] = (now + seconds, value)
