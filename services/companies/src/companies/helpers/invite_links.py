from testee_common.auth.user import User


def addressed_to(user: User | None, address: str) -> tuple[bool, str | None]:
    """Whether an invite link's address is the signed-in account's own, and the address itself
    only for that account with its email verified: a link never tells anyone else whom it was
    sent to (a sign-in that merely claims the address included)."""
    matches = user is not None and user.email.strip().lower() == address.lower()

    return matches, address if matches and user.email_verified else None
