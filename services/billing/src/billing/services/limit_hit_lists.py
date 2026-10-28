"""The AI costs tab's limits: ours and our providers', each with its hits in the period and the
companies and users that hit it most."""

from prepza_common.limits.limit_list import LIMITS
from prepza_common.limits.limits import OURS, current_values

from billing.constants.usage import TOP_HITTERS
from billing.integrations import names
from billing.integrations.redis import get_redis
from billing.models.usage import LimitHit
from billing.repositories import limit_hits
from billing.schemas.limits import HitterOut, LimitHitListsOut, LimitHitsOut
from billing.services.ai_costs import company_names


def top_by_limit(rows: list) -> dict[str, list[tuple[str, int]]]:
    found: dict[str, list[tuple[str, int]]] = {}

    for name, key, hits in rows:
        kept = found.setdefault(name, [])

        if len(kept) < TOP_HITTERS:
            kept.append((key, hits))

    return found


def hitters_out(found: list[tuple[str, int]], known: dict[str, str]) -> list[HitterOut]:
    return [HitterOut(id=key, name=known.get(key), hits=hits) for key, hits in found]


async def limit_hits_out(period: str | None) -> LimitHitListsOut:
    where = limit_hits.since(period)
    companies = top_by_limit(await limit_hits.hitters(LimitHit.company_id, where, TOP_HITTERS))
    users = top_by_limit(await limit_hits.hitters(LimitHit.user_id, where, TOP_HITTERS))
    company_ids = {key for found in companies.values() for key, _ in found}
    user_ids = {key for found in users.values() for key, _ in found}
    company_known = await company_names(list(company_ids))
    user_known = await names.user_emails(list(user_ids))
    values = await current_values(get_redis())
    lists = LimitHitListsOut(ours=[], providers=[])

    for name, kind, scope, hits in await limit_hits.counts(where):
        found = LIMITS.get(name)
        shown = LimitHitsOut(
            limit=name,
            kind=kind,
            scope=scope,
            value=values.get(name, found.default) if found else None,
            unit=found.unit if found else None,
            window=found.window if found else None,
            hits=hits,
            companies=hitters_out(companies.get(name, []), company_known),
            users=hitters_out(users.get(name, []), user_known),
        )
        (lists.ours if kind == OURS else lists.providers).append(shown)

    return lists
