from fastapi import APIRouter, status
from fastapi.encoders import jsonable_encoder
from prepza_common.auth.user import UserEmailIn

from companies.api.dependencies import ServiceCaller
from companies.repositories import accounts, companies
from companies.schemas.companies import UserCompaniesOut
from companies.services import accounts as account_service

router = APIRouter(prefix="/internal", tags=["internal"])


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str, body: UserEmailIn, caller: ServiceCaller) -> None:
    """Part of deleting an account (library coordinates it); safe to repeat."""
    await account_service.delete_user(user_id, body.email)


@router.post("/users/{user_id}/export")
async def export_user(user_id: str, body: UserEmailIn, caller: ServiceCaller) -> dict:
    return jsonable_encoder(await accounts.export(user_id, body.email))


@router.get("/users/{user_id}/companies")
async def user_companies(user_id: str, caller: ServiceCaller) -> UserCompaniesOut:
    """Every company the user is a member of, in any role; notifications sends them theirs."""
    return UserCompaniesOut(company_ids=await companies.ids_for_user(user_id))
