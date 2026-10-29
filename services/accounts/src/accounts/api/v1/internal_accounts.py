from fastapi import APIRouter, HTTPException, status
from prepza_common.auth.user import UserEmailIn

from accounts.api.dependencies import ServiceCaller
from accounts.helpers.accounts import account_out
from accounts.schemas.accounts import AccountOut, ProfilesIn, ProfilesOut
from accounts.services.accounts import account_by_email, account_by_id, profiles

# Companies, for the admin zone's support tab: who an account id or an address belongs to; and
# for an interview's notes, how their authors show themselves.
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


@router.post("/profiles")
async def get_profiles(body: ProfilesIn, caller: ServiceCaller) -> ProfilesOut:
    """Each account's name and picture, for the notes' authors; ids in the body, as a list."""
    return ProfilesOut(profiles=await profiles(body.user_ids))
