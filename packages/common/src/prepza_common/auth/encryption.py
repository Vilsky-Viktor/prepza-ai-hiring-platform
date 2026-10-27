from cryptography.fernet import Fernet, InvalidToken, MultiFernet


def keys(setting: str) -> MultiFernet:
    """A key setting (ATS_ENCRYPTION_KEY, SLACK_ENCRYPTION_KEY, ...): one Fernet key, or several
    separated by commas while one is being replaced, the new one first. Everything is sealed
    with the first; what any of them sealed can be read."""
    return MultiFernet([Fernet(key.strip()) for key in setting.split(",")])


def encrypt(key: str, text: str) -> str:
    """`text` encrypted with `key`'s first key (see `keys`)."""
    return keys(key).encrypt(text.encode()).decode()


def decrypt(key: str, token: str) -> str | None:
    """What `encrypt` sealed with any of `key`'s keys, or None when another key sealed it, it
    was changed, or the setting is missing or isn't Fernet keys."""
    try:
        return keys(key).decrypt(token.encode()).decode()
    except (InvalidToken, ValueError):
        return None
