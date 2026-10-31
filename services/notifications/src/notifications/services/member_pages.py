# The digest and reminders a page of companies at a time: each run of the day goes on after the
# last page a run finished (its cursor, in Redis), and stops at its deadline.
import time
from collections.abc import Awaitable, Callable
from datetime import date

from testee_common.http.capped import gather_capped

from notifications.constants.member_emails import CALLS_AT_ONCE, CURSOR_KEY, CURSOR_SECONDS
from notifications.integrations import companies
from notifications.integrations.redis import get_redis


async def cursor(job: str, day: date) -> str:
    """The last company id of the last page the day's runs of `job` finished; "" before any."""
    found = await get_redis().get(CURSOR_KEY.format(job=job, day=day.isoformat()))

    return found.decode() if found else ""


async def move_cursor(job: str, day: date, after: str) -> None:
    await get_redis().set(CURSOR_KEY.format(job=job, day=day.isoformat()), after, ex=CURSOR_SECONDS)


async def their_companies(user_ids: list[str]) -> list[str]:
    """Every company of these users, so each one's email covers all of theirs, whichever page
    found them."""
    found = await gather_capped(
        CALLS_AT_ONCE, (companies.company_ids(user_id) for user_id in user_ids)
    )

    return sorted({company_id for ids in found for company_id in ids})


async def each_page(
    job: str,
    day: date,
    read_page: Callable[[str], Awaitable[tuple[list[str], str]]],
    send_page: Callable[[list[str]], Awaitable[int]],
    stop: float,
) -> int:
    """Sends `job`'s emails of `day` a page of companies at a time until `stop`
    (time.monotonic()): read_page(after) gives the next page's company ids, after `after` in
    order, and where the page after it starts; send_page(company_ids) sends theirs and says how
    many went. A page done in time moves the cursor on; one cut short is done again by the next
    run, whose claims (member_sends.claim) skip who got theirs, so two runs at once send nothing
    twice either. Returns how many were sent."""
    after = await cursor(job, day)
    sent = 0

    while time.monotonic() < stop:
        company_ids, next_after = await read_page(after)

        if not company_ids:
            break

        sent += await send_page(company_ids)

        if time.monotonic() > stop:
            break

        await move_cursor(job, day, next_after)
        after = next_after

    return sent
