from prepza_common.http import http
from prepza_common.http.http import bearer

from notifications.constants.member_emails import MAX_IDS_PER_CALL


async def post_ids(
    url: str, token: str, field: str, ids: list[str], answer: str, extra: dict | None = None
) -> list:
    """Posts the ids to another service's batch route as `field` (with the `extra` fields),
    MAX_IDS_PER_CALL at a time (one call for the usual few), and returns the lists under `answer`
    together."""
    found = []

    for start in range(0, len(ids), MAX_IDS_PER_CALL):
        response = await http.get_client().post(
            url,
            json={field: ids[start : start + MAX_IDS_PER_CALL], **(extra or {})},
            headers=bearer(token),
        )
        response.raise_for_status()
        found += response.json()[answer]

    return found
