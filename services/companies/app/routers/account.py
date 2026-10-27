from fastapi import APIRouter
from prepza_common.auth.auth import CurrentUser

from app.schemas.account import AccountDeletionOut
from app.services import accounts

router = APIRouter(prefix="/account", tags=["account"])


@router.get("/deletion")
async def account_deletion(user: CurrentUser) -> AccountDeletionOut:
    """For the delete-account dialog: the companies that block deleting the account until
    another member owns them, and the ones deleted with it, with their credits."""
    return AccountDeletionOut(**await accounts.deletion(user.uid))
