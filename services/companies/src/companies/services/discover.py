from fastapi import HTTPException, status
from prepza_common.auth.user import User
from prepza_common.i18n.i18n import CodedError

from companies.constants import error_codes
from companies.constants.discover import DISCOVER_UNPAID
from companies.integrations import accounts, billing, library, rounds
from companies.models.companies import Company
from companies.models.interviews import Interview
from companies.schemas.discover import DiscoverPersonOut
from companies.services import candidate_invites
from companies.services import outbox as outbox_service
from companies.services.interview_access import ready_for_invites
from companies.services.interview_views import attach_set


async def require_paid(company_id) -> None:
    """Refused (403) to a company that never topped up, and when billing can't say."""
    if not await billing.company_paid(company_id):
        raise CodedError(status.HTTP_403_FORBIDDEN, DISCOVER_UNPAID, error_codes.DISCOVER_UNPAID)


async def people(interview: Interview, offset: int, limit: int) -> list[DiscoverPersonOut]:
    """A page of the people open to offers with practice results on the interview's subjects at
    its level (library matches the topics, rounds keeps who's open and their results); none
    while the interview has no questions yet."""
    await require_paid(interview.company_id)
    interview = await attach_set(interview)

    if interview.set_id is None:
        return []

    topic_ids = await library.practice_topics(interview.set_id)
    found = await rounds.offer_matches(topic_ids, offset, limit)

    return [
        DiscoverPersonOut(
            id=match["user_id"],
            name=match["name"],
            linkedin_url=match["linkedin_url"],
            results=match["results"],
        )
        for match in found
    ]


async def invite(interview: Interview, company: Company, user: User, person_id: str) -> None:
    """Invites the person through the usual invite (credits, email limits, the invite email to
    their account's address), while they're still open to offers; 404 once they aren't."""
    await require_paid(company.id)
    interview = await ready_for_invites(interview, user.uid)
    profile = await rounds.open_profile(person_id)
    account = await accounts.account(person_id) if profile else None

    if account is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")

    await candidate_invites.invite(interview, company, user, account["email"], profile["name"])
    await outbox_service.flush_quietly()
