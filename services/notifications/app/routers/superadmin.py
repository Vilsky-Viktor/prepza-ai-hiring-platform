from fastapi import APIRouter
from prepza_common.superadmin import SuperadminUser
from prepza_common.user import UserEmailIn

from app.schemas.unsubscribe import CandidateOptOutIn, CandidateOptOutsOut, CompanyOptOutOut
from app.services.admin_opt_outs import companies_for, set_stopped

# The admin zone's emails tab: a superadmin stops a company's emails to a candidate who asked
# prepza directly. Everyone else gets "not found". Addresses go in the body, never the query
# string, which request logs record.
router = APIRouter(prefix="/superadmin/candidate-opt-outs", tags=["superadmin"])


async def answer(email: str) -> CandidateOptOutsOut:
    return CandidateOptOutsOut(
        companies=[CompanyOptOutOut(**company) for company in await companies_for(email)]
    )


@router.post("/lookup")
async def look_up(body: UserEmailIn, superadmin: SuperadminUser) -> CandidateOptOutsOut:
    """The companies that invited the address or whose emails it stopped, by name."""
    return await answer(body.email)


@router.put("")
async def change(body: CandidateOptOutIn, superadmin: SuperadminUser) -> CandidateOptOutsOut:
    """Stops a company's emails to the address (only a company that invited it), or lets them
    through again; answers with the companies as the lookup does."""
    await set_stopped(body.email, str(body.company_id), body.stopped, superadmin.uid)

    return await answer(body.email)
