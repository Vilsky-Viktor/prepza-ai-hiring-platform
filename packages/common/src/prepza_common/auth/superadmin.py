# Superadmins: prepza's own team, not a company's admins. They manage templates and the question
# bank, and are the verified addresses listed in SUPERADMIN_EMAILS, comma-separated, signed in
# with Google (whose account security, two-step verification included, guards the admin zone):
# the same address signed in another way isn't one. Every service reads the same setting.
import logging
import os
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from prepza_common.auth.auth import fresh_user
from prepza_common.auth.user import User
from prepza_common.config.constants import GOOGLE_SIGN_IN

logger = logging.getLogger(__name__)


def is_superadmin(user: User) -> bool:
    emails = {email.strip().lower() for email in os.environ.get("SUPERADMIN_EMAILS", "").split(",")}

    return (
        user.email_verified
        and user.sign_in_provider == GOOGLE_SIGN_IN
        and user.email.lower() in emails - {""}
    )


def superadmin_user(request: Request, user: Annotated[User, Depends(fresh_user)]) -> User:
    """Not found for everyone else, so superadmin routes don't show they exist. A revoked
    sign-in is refused at once, reads included: the admin zone shows everyone's data. Every
    request is logged, by the account's id and the route's template (never what it looked up),
    which a log sink keeps in a locked bucket (infra/terraform/logging.tf)."""
    route = getattr(request.scope.get("route"), "path", request.url.path)

    if not is_superadmin(user):
        # Answered as not found, so it's logged here: someone tried the admin zone.
        logger.warning("Admin zone refused to account %s: %s %s", user.uid, request.method, route)

        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")

    logger.info("Admin zone used by account %s: %s %s", user.uid, request.method, route)

    return user


SuperadminUser = Annotated[User, Depends(superadmin_user)]
