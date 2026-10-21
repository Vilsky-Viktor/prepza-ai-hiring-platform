from prepza_common.names import clean_name

from app.constants.ats import (
    TEAMTAILOR_API_VERSION,
    TEAMTAILOR_CLOSED_JOBS,
    TEAMTAILOR_HOSTS,
    TEAMTAILOR_MAX_PAGES,
    TEAMTAILOR_MEDIA_TYPE,
    TEAMTAILOR_PAGE,
    AtsProvider,
)
from app.integrations.ats_http import checked, json_of, next_page, send
from app.integrations.errors import KeyRejected

# The credentials this client takes: the API (its company's region) and the API key.
KEYS = ("host", "key")
# Teamtailor's answers that mean the key is wrong, deleted, or lacks Admin or Write.
UNAVAILABLE = "Teamtailor didn't answer"


async def _call(method: str, host: str, key: str, path_or_url: str, params=None, body=None) -> dict:
    url = path_or_url if path_or_url.startswith("http") else host + path_or_url
    headers = {
        "Authorization": f"Token token={key}",
        "X-Api-Version": TEAMTAILOR_API_VERSION,
        "Accept": TEAMTAILOR_MEDIA_TYPE,
        "Content-Type": TEAMTAILOR_MEDIA_TYPE,
    }
    response = await send(
        method, url, headers, UNAVAILABLE, params, body, provider=AtsProvider.TEAMTAILOR
    )

    # A rate limit stays a 429, so a web hook is answered that way (Teamtailor may send it again
    # later) rather than as a failure of ours.
    return json_of(checked(response, UNAVAILABLE, passes_429=True))


async def _list(host: str, key: str, path: str, params: dict | None = None) -> list[dict]:
    """Every item of a list, following its next page (the answer's links.next)."""
    found: list[dict] = []
    url: str | None = path
    query: dict | None = {**(params or {}), "page[size]": TEAMTAILOR_PAGE}

    for _ in range(TEAMTAILOR_MAX_PAGES):
        answer = await _call("GET", host, key, url, query)
        found += answer.get("data", [])
        url = next_page((answer.get("links") or {}).get("next"), host, UNAVAILABLE)
        # The next page's address carries its own query.
        query = None

        if not url:
            break

    return found


async def region(key: str) -> tuple[str, str]:
    """The API of the key's region and its company's name; KeyRejected when no region accepts
    the key."""
    for host in TEAMTAILOR_HOSTS:
        try:
            company = await _call("GET", host, key, "/v1/company")
        except KeyRejected:
            continue

        return host, (company.get("data") or {}).get("attributes", {}).get("name", "")

    raise KeyRejected


async def check(host: str, key: str) -> None:
    """Raises KeyRejected unless the key may read users (Admin keys only)."""
    await _call("GET", host, key, "/v1/users", {"page[size]": 1})


async def jobs(host: str, key: str) -> list[dict]:
    """The jobs still hiring, as {id, name}."""
    found = await _list(host, key, "/v1/jobs")

    return [
        {"id": str(item["id"]), "name": item["attributes"].get("title", "")}
        for item in found
        if item["attributes"].get("status") not in TEAMTAILOR_CLOSED_JOBS
    ]


async def stages(host: str, key: str, job_id: str) -> list[dict]:
    """A job's stages in their order, as {id, name}."""
    found = await _list(host, key, f"/v1/jobs/{job_id}/stages")
    found.sort(key=lambda item: item["attributes"].get("row-order") or 0)

    return [{"id": str(item["id"]), "name": item["attributes"].get("name", "")} for item in found]


async def job(host: str, key: str, job_id: str) -> dict:
    """A job's title and its text (HTML): the pitch and the description."""
    found = (await _call("GET", host, key, f"/v1/jobs/{job_id}")).get("data") or {}
    attributes = found.get("attributes", {})

    return {
        "name": attributes.get("title", ""),
        "sections": [attributes.get("pitch") or "", attributes.get("body") or ""],
    }


async def application(host: str, key: str, application_id: str) -> dict:
    """A job application's job, stage and candidate (with their email and name), as Teamtailor has them
    now: a web hook only says one changed."""
    answer = await _call(
        "GET",
        host,
        key,
        f"/v1/job-applications/{application_id}",
        {"include": "candidate"},
    )
    relationships = (answer.get("data") or {}).get("relationships", {})

    def related(name: str) -> str | None:
        found = (relationships.get(name) or {}).get("data") or {}

        return str(found["id"]) if found.get("id") else None

    candidate = next(
        (item for item in answer.get("included", []) if item.get("type") == "candidates"), {}
    )

    attributes = candidate.get("attributes") or {}

    return {
        "job_id": related("job"),
        "stage_id": related("stage"),
        "candidate_id": related("candidate"),
        "email": attributes.get("email"),
        "name": clean_name(attributes.get("first-name"), attributes.get("last-name")),
    }


async def member_id(host: str, key: str, email: str) -> str | None:
    """The Teamtailor user results are written back as: the one with `email` (who connected),
    else the company's first admin, else its first user. No email (one not verified) looks no
    one up by it."""
    found = await _call("GET", host, key, "/v1/users", {"filter[email]": email}) if email else {}

    if found.get("data"):
        return str(found["data"][0]["id"])

    users = await _list(host, key, "/v1/users")
    admins = [user for user in users if user["attributes"].get("role") == "admin"]
    chosen = (admins or users or [None])[0]

    return str(chosen["id"]) if chosen else None


async def comment(host: str, key: str, candidate_id: str, member: str, text: str) -> None:
    """A note on the candidate in Teamtailor, as the user `member`."""
    body = {
        "data": {
            "type": "notes",
            "attributes": {"note": text},
            "relationships": {
                "candidate": {"data": {"type": "candidates", "id": candidate_id}},
                "user": {"data": {"type": "users", "id": member}},
            },
        }
    }
    await _call("POST", host, key, "/v1/notes", body=body)
