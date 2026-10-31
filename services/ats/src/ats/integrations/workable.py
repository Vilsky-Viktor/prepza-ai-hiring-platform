import httpx
from fastapi import status
from testee_common.http.http import bearer

from ats.constants.ats import (
    WORKABLE_API,
    WORKABLE_MAX_PAGES,
    WORKABLE_MOVED,
    WORKABLE_PAGE,
    AtsProvider,
)
from ats.integrations.ats_http import REJECTED, checked, json_of, send

# The credentials this client takes.
KEYS = ("subdomain", "token")
# Workable's answers that mean the key is wrong, revoked, expired or lacks a scope.
UNAVAILABLE = "Workable didn't answer"


async def _call(
    method: str,
    subdomain: str,
    token: str,
    path: str,
    params: dict | None = None,
    body: dict | None = None,
    rejected: set[int] = REJECTED,
) -> dict:
    """One call to Workable's API (ats_http: a refused key raises KeyRejected; something gone,
    a 404; anything else that fails, a 502 the caller can retry)."""
    url = WORKABLE_API.format(subdomain=subdomain) + path
    headers = bearer(token)
    response = await send(
        method, url, headers, UNAVAILABLE, params, body, provider=AtsProvider.WORKABLE
    )

    return json_of(checked(response, UNAVAILABLE, rejected))


async def _get(subdomain: str, token: str, path: str, params: dict | None = None) -> dict:
    return await _call("GET", subdomain, token, path, params)


async def check(subdomain: str, token: str) -> None:
    """Raises KeyRejected unless the key may read the account's jobs. An account that isn't
    there answers 404: the address is wrong, as good as a refused key."""
    rejected = REJECTED | {status.HTTP_404_NOT_FOUND}
    await _call("GET", subdomain, token, "/jobs", {"limit": 1}, rejected=rejected)


async def jobs(subdomain: str, token: str) -> list[dict]:
    """The account's published jobs, as {id, name}, a page at a time."""
    found: list[dict] = []
    params: dict = {"state": "published", "limit": WORKABLE_PAGE}

    for _ in range(WORKABLE_MAX_PAGES):
        page = await _get(subdomain, token, "/jobs", params)
        found += [{"id": job["shortcode"], "name": job["title"]} for job in page.get("jobs", [])]
        since_id = page.get("paging", {}).get("next")

        if not since_id:
            break

        # Workable's next page is a full address with since_id; only that parameter is kept.
        params = {**params, "since_id": httpx.URL(since_id).params.get("since_id")}

    return found


async def stages(subdomain: str, token: str, job_id: str) -> list[dict]:
    """A job's pipeline stages in order, as {id, name}."""
    page = await _get(subdomain, token, f"/jobs/{job_id}/stages")

    return [{"id": stage["slug"], "name": stage["name"]} for stage in page.get("stages", [])]


async def job(subdomain: str, token: str, job_id: str) -> dict:
    """One job: its title and its description, requirements and benefits (HTML)."""
    found = await _get(subdomain, token, f"/jobs/{job_id}")

    return {
        "name": found.get("title", ""),
        "sections": [found.get(key) or "" for key in ("description", "requirements", "benefits")],
    }


async def member_id(subdomain: str, token: str, email: str) -> str | None:
    """The Workable member results are written back as: the one with `email` (who connected),
    else the account's first admin, else its first member. No email (one not verified) looks
    no one up by it."""
    found = (
        (await _get(subdomain, token, "/members", {"email": email})).get("members", [])
        if email
        else []
    )

    if found:
        return found[0]["id"]

    members = (await _get(subdomain, token, "/members")).get("members", [])
    admins = [member for member in members if member.get("role") == "admin"]

    return (admins or members or [{"id": None}])[0]["id"]


async def subscribe(subdomain: str, token: str, target: str, job_id: str, stage_id: str) -> str:
    """Asks Workable to send candidates moved into `stage_id` of `job_id` to `target`; the
    subscription's id."""
    body = {
        "target": target,
        "event": WORKABLE_MOVED,
        "args": {"account_id": subdomain, "job_shortcode": job_id, "stage_slug": stage_id},
    }

    return str((await _call("POST", subdomain, token, "/subscriptions", body=body))["id"])


async def unsubscribe(subdomain: str, token: str, subscription_id: str) -> None:
    await _call("DELETE", subdomain, token, f"/subscriptions/{subscription_id}")


async def comment(subdomain: str, token: str, candidate_id: str, member: str, text: str) -> None:
    """A comment on the candidate in Workable, as `member`."""
    body = {"member_id": member, "comment": {"body": text}}
    await _call("POST", subdomain, token, f"/candidates/{candidate_id}/comments", body=body)
