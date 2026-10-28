import httpx
from prepza_common.http import http
from prepza_common.redis import memory_cache

from rounds.config import settings
from rounds.constants.help import CATALOG_CACHE_SECONDS, CATALOG_KEY


async def catalog(country: str | None = None) -> dict | None:
    """Billing's public prices in the currency of the visitor's `country` (US dollars without
    one), kept for a few minutes; None when billing can't be reached, so help still answers."""
    key = f"{CATALOG_KEY}:{country or ''}"
    cached = memory_cache.get(key)

    if cached is not None:
        return cached

    try:
        response = await http.get_client().get(
            f"{settings.billing_url}/catalog", params={"country": country} if country else None
        )
        response.raise_for_status()
    except httpx.HTTPError:
        return None

    prices = response.json()
    memory_cache.put(key, prices, CATALOG_CACHE_SECONDS)

    return prices
