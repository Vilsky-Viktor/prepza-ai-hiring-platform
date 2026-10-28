from prepza_common.auth.user import User


def candidate_email(user: User) -> str:
    """The email the services match the user's candidate data by: only a verified one, so a
    sign-in that merely claims an address can't erase or download another person's invites."""
    return user.email if user.email_verified else ""
