from billing.constants.currencies import Currency
from billing.constants.products import CANDIDATE_PRICES, CUSTOM_TOP_UP_MAX, TopUp


def candidate_tiers(currency: Currency) -> list[tuple[int, int]]:
    """A top-up of any number of candidates in `currency`: (from this many candidates, minor
    units per candidate), smallest first."""
    return CANDIDATE_PRICES[currency]


def candidate_price(candidates: int, currency: Currency) -> int:
    """What a candidate costs (minor units) in a top-up of this many: the price of the largest
    tier the count reaches."""
    return next(
        cents for count, cents in reversed(candidate_tiers(currency)) if candidates >= count
    )


def top_up_price(product: TopUp, currency: Currency) -> int:
    """What a fixed top-up costs in `currency` (minor units): its candidates at their price."""
    return product.candidates * candidate_price(product.candidates, currency)


def upgrade_from(index: int, currency: Currency) -> int | None:
    """From how many candidates a top-up in tier `index` costs at least the next tier's smallest
    one, which it then buys instead, so more candidates never cost less; None for the last."""
    tiers = candidate_tiers(currency)

    if index + 1 >= len(tiers):
        return None

    count, cents = tiers[index + 1]

    return -(-count * cents // tiers[index][1])


def custom_top_up(candidates: int, currency: Currency) -> tuple[int, int] | None:
    """A top-up of this many candidates in `currency`: the candidates it buys and what each
    costs (minor units), each at the price of the largest tier the count reaches, or the next
    tier's smallest top-up when that costs no more; None outside the range sold."""
    tiers = candidate_tiers(currency)

    if not tiers[0][0] <= candidates <= CUSTOM_TOP_UP_MAX:
        return None

    index = max(i for i, (count, _) in enumerate(tiers) if candidates >= count)
    upgrade = upgrade_from(index, currency)

    if upgrade is not None and candidates >= upgrade:
        return tiers[index + 1]

    return candidates, tiers[index][1]
