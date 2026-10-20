from prepza_common.constants import CREDITS_PER_DOLLAR

from app.constants.credits import CANDIDATE_CREDITS
from app.constants.products import CANDIDATE_PRICE_TIERS, CUSTOM_TOP_UP_MAX, TOP_UPS

# A candidate's price outside the volume tiers: $5.
BASE_CANDIDATE_CENTS = CANDIDATE_CREDITS * 100 // CREDITS_PER_DOLLAR


def credits_for(price_cents: int) -> int:
    """What a top-up of this amount buys: its candidates at its volume price, in credits; one
    rule for every amount."""
    cents = next(
        (price for floor, price in CANDIDATE_PRICE_TIERS if price_cents >= floor),
        BASE_CANDIDATE_CENTS,
    )

    return price_cents * CANDIDATE_CREDITS // cents


def candidate_prices() -> list[tuple[int, int]]:
    """What a candidate costs in money at each volume tier: (top-up from, in dollars; cents per
    candidate), cheapest last."""
    tiers = sorted(CANDIDATE_PRICE_TIERS)

    return [(1, BASE_CANDIDATE_CENTS)] + [(floor // 100, price) for floor, price in tiers]


def candidate_tiers() -> list[tuple[int, int]]:
    """A top-up of any number of candidates: (from this many candidates, cents per candidate),
    one per fixed top-up, at its size and price; smallest first."""
    tiers = [
        (credits_for(product.price_cents) // CANDIDATE_CREDITS, product.price_cents)
        for product in TOP_UPS
    ]

    return [(count, price // count) for count, price in sorted(tiers)]


def upgrade_from(index: int) -> int | None:
    """From how many candidates a top-up in tier `index` costs at least the next tier's smallest
    one, which it then buys instead, so more candidates never cost less; None for the last."""
    tiers = candidate_tiers()

    if index + 1 >= len(tiers):
        return None

    count, cents = tiers[index + 1]

    return -(-count * cents // tiers[index][1])


def custom_top_up(candidates: int) -> tuple[int, int] | None:
    """A top-up of this many candidates: the candidates it buys and what each costs (cents),
    each at the price of the largest tier the count reaches, or the next tier's smallest top-up
    when that costs no more; None outside the range sold."""
    tiers = candidate_tiers()

    if not tiers[0][0] <= candidates <= CUSTOM_TOP_UP_MAX:
        return None

    index = max(i for i, (count, _) in enumerate(tiers) if candidates >= count)
    upgrade = upgrade_from(index)

    if upgrade is not None and candidates >= upgrade:
        return tiers[index + 1]

    return candidates, tiers[index][1]
