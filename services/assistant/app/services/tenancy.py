import httpx
from fastapi import HTTPException, status
from prepza_common.redis import memory_cache

from app.constants.chat import CHAT_FAILED, COMPANY_NOT_FOUND
from app.constants.tenancy import COMPANIES_KEY, COMPANIES_SECONDS
from app.integrations import companies


async def user_companies(user_id: str, fresh: bool = False) -> frozenset[str]:
    """The ids of every company the user is a member of, from companies' own list (no page
    limit), kept COMPANIES_SECONDS so a confirm reads it once; `fresh` after an action that may
    have made one. A 503 when companies doesn't answer. The panel and AI apps both check with
    it."""
    key = COMPANIES_KEY.format(user_id=user_id)
    found = None if fresh else memory_cache.get(key)

    if found is None:
        try:
            found = frozenset(await companies.company_ids(user_id))
        except httpx.HTTPError:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, CHAT_FAILED) from None

        memory_cache.put(key, found, COMPANIES_SECONDS)

    return found


def require_company(company_id, companies: frozenset[str]) -> None:
    """Refuses (404) a company that isn't one of the user's, before anything is called with it."""
    if company_id is not None and str(company_id) not in companies:
        raise HTTPException(status.HTTP_404_NOT_FOUND, COMPANY_NOT_FOUND)


def foreign_company(arguments: dict, companies: frozenset[str]) -> bool:
    """Whether a tool's arguments name a company that isn't one of the user's."""
    company_id = arguments.get("company_id")

    return company_id is not None and str(company_id) not in companies
