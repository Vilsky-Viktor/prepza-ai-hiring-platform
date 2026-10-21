import hashlib
import time

import httpx
from fastapi import HTTPException, status
from prepza_common import http
from prepza_common.http import bearer

from app.constants.ats import (
    ATS_TIMEOUT_SECONDS,
    GREENHOUSE_API,
    GREENHOUSE_INTROSPECT_URL,
    GREENHOUSE_MAX_PAGES,
    GREENHOUSE_NOTES_SCOPE,
    GREENHOUSE_PAGE,
    GREENHOUSE_TOKEN_MARGIN_SECONDS,
    GREENHOUSE_TOKEN_URL,
    AtsProvider,
)
from app.integrations.ats_http import REJECTED, checked, next_page, note_busy, send

# The credentials this client takes (a connection also keeps its web hook's secret key).
KEYS = ("client_id", "client_secret")
# Greenhouse's answers that mean the credential is wrong, revoked or lacks a permission.
UNAVAILABLE = "Greenhouse didn't answer"
# Its token endpoint (OAuth) answers a wrong or revoked credential with 400 too. On any other
# call a 400 is a request it didn't take (one note, one candidate), not a refused key.
TOKEN_REJECTED = REJECTED | {status.HTTP_400_BAD_REQUEST}
# Access tokens by credential (client id and a hash of its secret, so another company's cached
# token is never used for a wrong secret), with when each stops being used: about an hour.
_tokens: dict[tuple[str, str], tuple[str, float]] = {}


async def _token(client_id: str, client_secret: str, fresh: bool = False) -> str:
    """An access token for the credential (client credentials grant), kept until shortly before
    it expires."""
    credential = (client_id, hashlib.sha256(client_secret.encode()).hexdigest())
    kept = _tokens.get(credential)

    if kept and not fresh and kept[1] > time.monotonic():
        return kept[0]

    try:
        response = await http.get_client().post(
            GREENHOUSE_TOKEN_URL,
            auth=(client_id, client_secret),
            data={"grant_type": "client_credentials"},
            timeout=ATS_TIMEOUT_SECONDS,
        )
    except httpx.HTTPError as error:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, UNAVAILABLE) from error

    await note_busy(response, AtsProvider.GREENHOUSE)
    checked(response, UNAVAILABLE, TOKEN_REJECTED)
    body = response.json()
    expires = time.monotonic() + body.get("expires_in", 3600) - GREENHOUSE_TOKEN_MARGIN_SECONDS
    _tokens[credential] = (body["access_token"], expires)

    return body["access_token"]


async def _call(
    method: str,
    client_id: str,
    client_secret: str,
    url: str,
    params: dict | None = None,
    body: dict | None = None,
    rejected: set[int] = REJECTED,
) -> httpx.Response:
    """One call to the Harvest API; a 401 renews the token once (it may have expired early). A
    404 is what was asked for being gone (a candidate deleted), not a refused key."""
    for fresh in (False, True):
        token = await _token(client_id, client_secret, fresh)
        headers = bearer(token)
        response = await send(
            method, url, headers, UNAVAILABLE, params, body, provider=AtsProvider.GREENHOUSE
        )

        if response.status_code != status.HTTP_401_UNAUTHORIZED:
            break

    return checked(response, UNAVAILABLE, rejected)


def _items(response: httpx.Response) -> list[dict]:
    """A list answer's items, whether the list comes bare or under "data"."""
    body = response.json() if response.content else []

    return body if isinstance(body, list) else body.get("data", [])


async def _list(client_id: str, client_secret: str, path: str, params: dict) -> list[dict]:
    """Every item of a list endpoint, following its next page (the Link header)."""
    found: list[dict] = []
    url: str | None = GREENHOUSE_API + path
    query: dict | None = {**params, "per_page": GREENHOUSE_PAGE}

    for _ in range(GREENHOUSE_MAX_PAGES):
        response = await _call("GET", client_id, client_secret, url, query)
        found += _items(response)
        url = next_page(response.links.get("next", {}).get("url"), GREENHOUSE_API, UNAVAILABLE)
        # The next page's address carries its own query.
        query = None

        if not url:
            break

    return found


async def check(client_id: str, client_secret: str) -> None:
    """Raises KeyRejected unless the credential may read jobs (any refusal counts here)."""
    url = GREENHOUSE_API + "/jobs"
    rejected = TOKEN_REJECTED | {status.HTTP_404_NOT_FOUND}
    await _call("GET", client_id, client_secret, url, {"per_page": 1}, rejected=rejected)


async def can_write(client_id: str, client_secret: str) -> bool:
    """False only when Greenhouse says the credential's token lacks the scope a note needs: its
    introspection lists the token's scopes. Any other answer (an error, no list) lets it
    connect; a refused note tells then (services/ats.py WriteRefused)."""
    token = await _token(client_id, client_secret)

    try:
        response = await http.get_client().post(
            GREENHOUSE_INTROSPECT_URL,
            auth=(client_id, client_secret),
            data={"token": token, "token_type_hint": "access_token"},
            timeout=ATS_TIMEOUT_SECONDS,
        )
        body = response.json()
    except (httpx.HTTPError, ValueError):
        return True

    if not isinstance(body, dict) or body.get("active") is not True:
        return True

    scope = body.get("scope")

    if not isinstance(scope, str):
        return True

    return GREENHOUSE_NOTES_SCOPE in scope.split()


async def jobs(client_id: str, client_secret: str) -> list[dict]:
    """The open jobs, as {id, name}."""
    found = await _list(client_id, client_secret, "/jobs", {"status": "open"})

    return [{"id": str(job["id"]), "name": job.get("name", "")} for job in found]


async def stages(client_id: str, client_secret: str, job_id: str) -> list[dict]:
    """A job's interview stages in order, as {id, name}."""
    found = await _list(client_id, client_secret, "/job_interview_stages", {"job_ids": job_id})

    return [{"id": str(stage["id"]), "name": stage.get("name", "")} for stage in found]


async def job(client_id: str, client_secret: str, job_id: str) -> dict:
    """A job's name and its job posts' text (HTML)."""
    found = await _list(client_id, client_secret, "/jobs", {"ids": job_id})
    posts = await _list(client_id, client_secret, "/job_posts", {"job_ids": job_id})

    return {
        "name": found[0].get("name", "") if found else "",
        "sections": [post.get("content") or "" for post in posts],
    }


async def comment(
    client_id: str, client_secret: str, candidate_id: str, member: str | None, text: str
) -> None:
    """A note on the candidate's activity feed. `candidate_id` is "<candidate>:<application>"
    as the web hook gave them."""
    candidate, _, application = candidate_id.partition(":")
    body = {
        "candidate_id": int(candidate),
        "body": text,
        "note_type": "NOTE",
        "visibility": "public",
    }

    if application:
        body["application_id"] = int(application)

    if member:
        body["user_id"] = int(member)

    await _call("POST", client_id, client_secret, GREENHOUSE_API + "/notes", body=body)
