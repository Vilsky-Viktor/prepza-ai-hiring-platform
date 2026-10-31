# Who may do what in a company, as the companies service answers it. The api, ats and
# notifications guard company pages with it, and keep API keys, web hooks and Slack working only
# while whoever made them is still an owner or admin.
from contextvars import ContextVar
from typing import Annotated

from fastapi import Header, HTTPException, status
from testee_common.config.constants import ASSISTANT_HEADER
from testee_common.http import http
from testee_common.http.http import bearer

# The X-Assistant header of the request being served: what it came through when the assistant or
# an AI app made it, passed on to companies, which refuses as its own routes do (an AI app while
# the company doesn't allow them). Only companies can read it.
assistant_token: ContextVar[str | None] = ContextVar("assistant_token", default=None)


async def remember_assistant(
    x_assistant: Annotated[str | None, Header(include_in_schema=False)] = None,
) -> None:
    """Every request's, run for the whole app, so each access check passes it on."""
    assistant_token.set(x_assistant)


async def access(companies_url: str, token: str, company_id, user_id: str) -> dict:
    """What the user may do in the company: {"member", "editor", "refused", "read_only"} (an
    editor is an owner or admin; see `require`). A company that's gone is one nobody may do
    anything in; companies failing otherwise raises."""
    headers = bearer(token)
    via = assistant_token.get()

    if via:
        headers[ASSISTANT_HEADER] = via

    response = await http.get_client().get(
        f"{companies_url}/internal/companies/{company_id}/access",
        params={"user_id": user_id},
        headers=headers,
    )

    if response.status_code == status.HTTP_404_NOT_FOUND:
        return {"member": False, "editor": False}

    response.raise_for_status()

    return response.json()


def require(found: dict, editor: bool) -> None:
    """A member may look; only an editor may change. Others get 404, as if the company weren't
    there; a viewer changing gets 403. What companies refuses anyway is 403 with its reason: any
    request through an AI app the company doesn't allow, and a change while it's suspended."""
    if not found["member"]:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Company not found")

    if found.get("refused"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, found["refused"])

    if editor and not found["editor"]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Viewers can't change anything here")

    if editor and found.get("read_only"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, found["read_only"])
