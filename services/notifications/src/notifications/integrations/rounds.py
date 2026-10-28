from prepza_common.http import http
from prepza_common.http.http import bearer

from notifications.config import settings
from notifications.core.security import service_token


async def user_ids(group: str, after: str) -> list[str]:
    """A page of the candidates (people who took a company's interview) or the learners (people
    who took a free practice round), as `group` says, the ids after `after` in order
    (prepza_common.db.paging), for a campaign to them."""
    response = await http.get_client().get(
        f"{settings.rounds_url}/internal/users/ids",
        params={"group": group, "after": after},
        headers=bearer(service_token("rounds")),
    )
    response.raise_for_status()

    return response.json()["user_ids"]
