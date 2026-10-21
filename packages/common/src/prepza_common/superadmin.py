# Superadmins: prepza's own team, not a company's admins. They manage templates and the question
# bank, and are the verified addresses listed in SUPERADMIN_EMAILS, comma-separated, signed in
# with Google (whose account security, two-step verification included, guards the admin zone):
# the same address signed in another way isn't one. Every service reads the same setting.
import os
from typing import Annotated

from fastapi import Depends, HTTPException, status
from prepza_common.auth import fresh_user
from prepza_common.constants import GOOGLE_SIGN_IN
from prepza_common.user import User


def is_superadmin(user: User) -> bool:
    emails = {email.strip().lower() for email in os.environ.get("SUPERADMIN_EMAILS", "").split(",")}

    return (
        user.email_verified
        and user.sign_in_provider == GOOGLE_SIGN_IN
        and user.email.lower() in emails - {""}
    )


def superadmin_user(user: Annotated[User, Depends(fresh_user)]) -> User:
    """Not found for everyone else, so superadmin routes don't show they exist. A revoked
    sign-in is refused at once, reads included: the admin zone shows everyone's data."""
    if not is_superadmin(user):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")

    return user


SuperadminUser = Annotated[User, Depends(superadmin_user)]
