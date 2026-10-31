from fastapi import status
from testee_common.http.http import bearer

from ats.constants.ats import RECRUITEE_API, RECRUITEE_OPEN_JOBS, AtsProvider
from ats.integrations.ats_http import REJECTED, checked, json_of, send

# The credentials this client takes: the company (its subdomain) and a personal API token, which
# acts as the person who made it.
KEYS = ("company", "token")
# Recruitee's answers that mean the token is wrong, revoked, or its person can't see that.
UNAVAILABLE = "Recruitee didn't answer"


async def _call(
    method: str, company: str, token: str, path: str, params=None, body=None, rejected=REJECTED
) -> dict:
    url = RECRUITEE_API.format(company=company) + path
    headers = bearer(token)
    response = await send(
        method, url, headers, UNAVAILABLE, params, body, provider=AtsProvider.RECRUITEE
    )

    return json_of(checked(response, UNAVAILABLE, rejected))


async def check(company: str, token: str) -> None:
    """Raises KeyRejected unless the token may read the company's jobs. A company that isn't
    there answers 404: the address is wrong, as good as a refused key."""
    rejected = REJECTED | {status.HTTP_404_NOT_FOUND}
    await _call("GET", company, token, "/offers", {"limit": 1}, rejected=rejected)


async def jobs(company: str, token: str) -> list[dict]:
    """The jobs still hiring (published, or internal only), as {id, name}."""
    found = await _call("GET", company, token, "/offers", {"statuses[]": RECRUITEE_OPEN_JOBS})

    return [
        {"id": str(offer["id"]), "name": offer.get("title", "")}
        for offer in found.get("offers", [])
        if offer.get("kind", "job") == "job"
    ]


async def _offer(company: str, token: str, job_id: str) -> dict:
    return (await _call("GET", company, token, f"/offers/{job_id}")).get("offer") or {}


async def stages(company: str, token: str, job_id: str) -> list[dict]:
    """A job's stages in its pipeline's order, as {id, name}."""
    offer = await _offer(company, token, job_id)
    found = (offer.get("pipeline_template") or {}).get("stages", [])
    found = sorted(found, key=lambda stage: stage.get("position") or 0)

    return [{"id": str(stage["id"]), "name": stage.get("name", "")} for stage in found]


async def job(company: str, token: str, job_id: str) -> dict:
    """A job's title and its text (HTML): the description and the requirements."""
    offer = await _offer(company, token, job_id)

    return {
        "name": offer.get("title", ""),
        "sections": [offer.get("description") or "", offer.get("requirements") or ""],
    }


async def comment(
    company: str, token: str, candidate_id: str, member: str | None, text: str
) -> None:
    """A note on the candidate in Recruitee, as the person whose token it is."""
    body = {"note": {"body": text, "visibility": {"level": "public"}}}
    await _call("POST", company, token, f"/candidates/{candidate_id}/notes", body=body)
