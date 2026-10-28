"""The admin zone's support search: what a superadmin pastes from a complaint, resolved to the
accounts, companies, interviews and candidates it points at."""

from uuid import UUID

from companies.constants.superadmin import (
    COMPANY_PATH,
    SUPPORT_RESULTS,
    TRANSACTION_ID,
    QueryKind,
    SupportKind,
)
from companies.integrations import billing, library
from companies.repositories import companies, superadmin_companies, superadmin_support
from companies.schemas.superadmin_support import SupportResultOut


def kind_of(query: str) -> str:
    if COMPANY_PATH.search(query):
        return QueryKind.LINK

    if as_uuid(query) is not None:
        return QueryKind.ID

    if TRANSACTION_ID.fullmatch(query):
        return QueryKind.TRANSACTION

    return QueryKind.EMAIL if "@" in query else QueryKind.NAME


def as_uuid(text: str | None) -> UUID | None:
    try:
        return UUID(text)
    except (TypeError, ValueError):
        return None


def company_result(company) -> SupportResultOut:
    return SupportResultOut(
        kind=SupportKind.COMPANY,
        id=str(company.id),
        title=company.name,
        company_id=company.id,
        company_name=company.name,
    )


def candidate_result(invite, company) -> SupportResultOut:
    return SupportResultOut(
        kind=SupportKind.CANDIDATE,
        id=str(invite.id),
        title=invite.email,
        company_id=company.id,
        company_name=company.name,
    )


def user_result(account: dict | None) -> list[SupportResultOut]:
    """The account, titled by its address (by its id when it has none: a guest candidate)."""
    if account is None:
        return []

    return [
        SupportResultOut(
            kind=SupportKind.USER,
            id=account["user_id"],
            title=account["email"] or account["user_id"],
        )
    ]


async def company_by_id(company_id: UUID) -> list[SupportResultOut]:
    company = await companies.get(company_id)

    return [company_result(company)] if company else []


async def interview_by_id(interview_id: UUID) -> list[SupportResultOut]:
    found = await superadmin_support.interview(interview_id)

    if found is None:
        return []

    interview, company = found

    return [
        SupportResultOut(
            kind=SupportKind.INTERVIEW,
            id=str(interview.id),
            title=interview.title or "",
            company_id=company.id,
            company_name=company.name,
        )
    ]


async def candidate_by_id(invite_id: UUID) -> list[SupportResultOut]:
    found = await superadmin_support.candidate(invite_id)

    if found is None:
        return []

    invite, _, company = found

    return [candidate_result(invite, company)]


async def by_link(query: str) -> list[SupportResultOut]:
    """The deepest page the link points at: a candidate, else an interview, else a company."""
    company_id, interview_id, invite_id = COMPANY_PATH.search(query).groups()

    if invite_id:
        return await candidate_by_id(UUID(invite_id))

    if interview_id:
        return await interview_by_id(UUID(interview_id))

    return await company_by_id(UUID(company_id))


async def by_id(query: str) -> list[SupportResultOut]:
    """Whatever has that id: ids are random, so at most one of them in practice."""
    found = as_uuid(query)

    return await company_by_id(found) + await interview_by_id(found) + await candidate_by_id(found)


async def by_transaction(query: str) -> list[SupportResultOut]:
    """The company a top-up's transaction paid into, as billing knows it."""
    owner = await billing.purchase_owner(query)
    company_id = as_uuid(owner["owner_id"]) if owner else None

    return await company_by_id(company_id) if company_id else []


async def by_email(query: str) -> list[SupportResultOut]:
    """The account signed in with that address, companies with a member of it, and candidates
    invited at it."""
    found = user_result(await library.account_by_email(query)) + [
        company_result(company)
        for company in await superadmin_support.companies_of_member(query, SUPPORT_RESULTS)
    ]

    return found + [
        candidate_result(invite, company)
        for invite, company in await superadmin_support.invites_to(query, SUPPORT_RESULTS)
    ]


async def by_name(query: str) -> list[SupportResultOut]:
    """The account with that id (from "copy id" in its menu or Settings) and the companies it's
    a member of, then companies whose name contains it: an account id reads like a short
    name."""
    members = [
        company for company, _ in await superadmin_support.companies_of_user(query, SUPPORT_RESULTS)
    ]
    named = [company for company, _ in await superadmin_companies.search(query, SUPPORT_RESULTS)]
    ids = {company.id for company in members}

    return user_result(await library.account(query)) + [
        company_result(company)
        for company in members + [company for company in named if company.id not in ids]
    ]


SEARCHES = {
    QueryKind.LINK: by_link,
    QueryKind.ID: by_id,
    QueryKind.TRANSACTION: by_transaction,
    QueryKind.EMAIL: by_email,
    QueryKind.NAME: by_name,
}


async def search(query: str) -> list[SupportResultOut]:
    """At most SUPPORT_RESULTS; unknown ids find nothing."""
    found = await SEARCHES[kind_of(query)](query)

    return found[:SUPPORT_RESULTS]
