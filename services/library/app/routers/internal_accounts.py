from fastapi import APIRouter, HTTPException, status
from prepza_common.auth.user import UserEmailIn

from app.helpers.accounts import account_out
from app.schemas.accounts import AccountOut
from app.service_auth import ServiceCaller
from app.services.accounts import account_by_email, account_by_id

# Companies, for the admin zone's support tab: who an account id or an address belongs to.
# Addresses go in the body, never the query string, which request logs record.
router = APIRouter(prefix="/internal/accounts", tags=["internal"])


@router.get("/{user_id}")
async def get_account(user_id: str, caller: ServiceCaller) -> AccountOut:
    """404 when there's no account with that id."""
    account = await account_by_id(user_id)

    if account is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")

    return account_out(account)


@router.post("/lookup")
async def look_up(body: UserEmailIn, caller: ServiceCaller) -> AccountOut:
    """The account signed in with the address, whatever its case; 404 when there's none."""
    account = await account_by_email(body.email)

    if account is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")

    return account_out(account)
