import asyncio
from datetime import datetime

import httpx
from prepza_common.config.constants import VIA_MCP
from prepza_common.i18n.i18n import translate

from app.constants.tool_calls import SERVICE_UNAVAILABLE
from app.constants.updates import (
    CANDIDATE_UPDATES_PATH,
    NOT_INVITED_PATH,
    QUESTION_UPDATES_PATH,
    UPDATES_PATH,
)
from app.helpers.updates import counts_of, credits_low, events_of, updates_result
from app.integrations import billing, services
from app.integrations import update_sources as sources
from app.services.tool_calls import error_content


class Refused(Exception):
    """A call get_updates can't answer, with its status and why, in the user's language."""

    def __init__(self, status: int, detail: str) -> None:
        self.status = status
        self.detail = detail


async def user_companies(token: str, language: str, via: str) -> dict[str, dict]:
    """The user's companies by id, read with their token (an API key's own only); for an AI
    app, only those that allow AI apps."""
    try:
        response = await services.get("companies", "/companies", {}, token, language, via=via)
    except httpx.HTTPError:
        raise Refused(503, translate(SERVICE_UNAVAILABLE, language)) from None

    if not response.is_success:
        raise Refused(response.status_code, error_content(response, language)["detail"])

    return {
        company["id"]: company
        for company in response.json()
        if company["ai_apps_allowed"] or via != VIA_MCP
    }


async def read(
    arguments: dict,
    token: str,
    language: str,
    period: tuple[datetime, datetime],
    via: str,
    site: str,
    sees_credits: bool,
) -> dict:
    """The updates between the two times in the companies the call may read (only
    `company_id`'s when it names one), each from the service that holds it (see
    constants/updates.py), and, where the user may see credits (an owner or admin; a key with
    credits:read), whether they run low."""
    found = await user_companies(token, language, via)

    if arguments.get("company_id"):
        found = {key: company for key, company in found.items() if key == arguments["company_id"]}

    ids = list(found)
    editors = [key for key, company in found.items() if company["can_edit"] and sees_credits]

    if not ids:
        return updates_result([], {}, [], {}, period[0], site)

    calls = [
        sources.updates("companies", CANDIDATE_UPDATES_PATH, ids, period),
        sources.updates("ats", NOT_INVITED_PATH, ids, period),
        sources.updates("library", QUESTION_UPDATES_PATH, ids, period),
        sources.updates("notifications", UPDATES_PATH, ids, period),
    ]

    if editors:
        calls.append(billing.low_companies(editors))

    try:
        answers = await asyncio.gather(*calls)
    except httpx.HTTPError:
        raise Refused(503, translate(SERVICE_UNAVAILABLE, language)) from None

    candidates, not_invited, questions, bell = answers[:4]
    low = [credits_low(company) for company in (answers[4] if editors else [])]
    names = {key: company["name"] for key, company in found.items()}
    events = events_of(candidates["items"], not_invited["items"], questions["items"], bell["items"])
    counts = counts_of(candidates, not_invited, questions, events)

    return updates_result(events, counts, low, names, period[0], site)
