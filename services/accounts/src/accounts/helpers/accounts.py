from datetime import UTC, datetime

from testee_common.auth.user import User

from accounts.schemas.accounts import AccountOut


def candidate_email(user: User) -> str:
    """The email the services match the user's candidate data by: only a verified one, so a
    sign-in that merely claims an address can't erase or download another person's invites."""
    return user.email if user.email_verified else ""


def account_out(account) -> AccountOut:
    """A Firebase account; it keeps its creation time in milliseconds."""
    created = account.user_metadata.creation_timestamp if account.user_metadata else None

    return AccountOut(
        user_id=account.uid,
        email=account.email,
        created_at=datetime.fromtimestamp(created / 1000, UTC) if created else None,
    )
