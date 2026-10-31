from fastapi import APIRouter
from testee_common.auth.superadmin import SuperadminUser
from testee_common.auth.user import UserEmailIn

from notifications.schemas.suppression import SuppressionOut
from notifications.services import suppression

# The support tab's account page: whether bulk sends skip the account's address (it bounced or
# marked an email as spam), and taking it off the list. Everyone else gets "not found". The
# address goes in the body, which request logs don't record.
router = APIRouter(prefix="/superadmin/suppressed", tags=["superadmin"])


async def answer(email: str) -> SuppressionOut:
    found = await suppression.lookup(email)

    return SuppressionOut(**(found or {"reason": None, "created_at": None}))


@router.post("/lookup")
async def look_up(body: UserEmailIn, superadmin: SuperadminUser) -> SuppressionOut:
    return await answer(body.email)


@router.post("/remove")
async def remove(body: UserEmailIn, superadmin: SuperadminUser) -> SuppressionOut:
    """Safe to repeat."""
    await suppression.remove(body.email, superadmin.uid)

    return await answer(body.email)
