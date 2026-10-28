from uuid import UUID

import httpx
from fastapi import HTTPException, status

from assistant.constants.chat import CHAT_FAILED
from assistant.constants.welcome import WELCOME_LIMIT, Stage
from assistant.helpers.welcome import stage
from assistant.integrations import services


async def read(path: str, query: dict, token: str, language: str) -> list[dict]:
    """A list from companies, as the user; a 503 when it doesn't answer."""
    try:
        response = await services.get("companies", path, query, token, language)
    except httpx.HTTPError:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, CHAT_FAILED) from None

    if not response.is_success:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, CHAT_FAILED)

    found = response.json()

    return found if isinstance(found, list) else [found]


async def welcome_stage(company_id: UUID | None, token: str, language: str) -> Stage:
    """The user's stage, from what companies shows them: their companies (or the one of the page
    they're on) and, for those with interviews, whether any interview has candidates."""
    if company_id is None:
        companies = await read("/companies", {"limit": WELCOME_LIMIT}, token, language)
    else:
        companies = await read(f"/companies/{company_id}", {}, token, language)

    has_candidates = False

    for company in companies:
        if company.get("interview_count"):
            query = {"company_id": company["id"], "limit": WELCOME_LIMIT}
            interviews = await read("/interviews", query, token, language)

            if any(interview.get("candidate_count") for interview in interviews):
                has_candidates = True

                break

    return stage(companies, has_candidates)
