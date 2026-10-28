from billing.constants.events import CREDITS_ADDED


def credits_added(owner_type: str, owner_id: str) -> tuple[str, dict]:
    """The event that tells other services the owner got credits (the ATS's candidates kept for
    lack of them are invited), saved through the outbox with the credits themselves."""
    return CREDITS_ADDED, {"owner_type": owner_type, "owner_id": owner_id}
