from billing.config import settings
from billing.constants.credits import CANDIDATE_CREDITS, REFERRAL_REWARD, WELCOME_COMPANY
from billing.constants.currencies import DEFAULT_CURRENCY, Currency
from billing.constants.products import (
    CUSTOM_TOP_UP_FLAG,
    CUSTOM_TOP_UP_KEY,
    CUSTOM_TOP_UP_MAX,
    TOP_UP_FLAG,
    TOP_UPS,
)
from billing.helpers.credits import candidate_price, candidate_tiers, top_up_price, upgrade_from
from billing.helpers.item_names import candidates_name
from billing.schemas.billing import (
    CandidatePriceOut,
    CandidateTierOut,
    CatalogOut,
    CustomTopUpOut,
    TopUpOut,
)


def catalog_out(currency: Currency) -> CatalogOut:
    """Every price, in `currency`."""
    tiers = candidate_tiers(currency)
    cents = [price for _, price in tiers]

    return CatalogOut(
        environment=settings.paddle_environment,
        client_token=settings.paddle_client_token,
        currency=currency,
        candidate_credits=CANDIDATE_CREDITS,
        candidate_prices=[
            CandidatePriceOut(from_cents=count * price, cents=price) for count, price in tiers
        ],
        candidate_cents_min=min(cents),
        candidate_cents_max=max(cents),
        welcome_company=WELCOME_COMPANY,
        free_candidates=WELCOME_COMPANY // CANDIDATE_CREDITS,
        referral_company=REFERRAL_REWARD,
        products=[
            TopUpOut(
                key=product.key,
                price_cents=top_up_price(product, currency),
                credits=product.candidates * CANDIDATE_CREDITS,
                candidates=product.candidates,
                candidate_cents=candidate_price(product.candidates, currency),
            )
            for product in TOP_UPS
        ],
        custom=CustomTopUpOut(
            min_candidates=tiers[0][0],
            max_candidates=CUSTOM_TOP_UP_MAX,
            on_sale=bool(settings.paddle_product_candidates),
            tiers=[
                CandidateTierOut(
                    from_candidates=count,
                    cents=price,
                    upgrade_from=upgrade_from(index, currency),
                )
                for index, (count, price) in enumerate(tiers)
            ],
        ),
    )


def candidates_price(
    candidates: int, cents: int, currency: Currency, top_up: str | None, language: str
) -> dict:
    """Paddle's price, made in the transaction itself, of a top-up of `candidates` at `cents`
    each in `currency` only, so Paddle charges that currency wherever the buyer is: one item the
    buyer can't change, its tax added on top, named in the buyer's `language` (checkout and
    invoice show it). What it buys is in its custom data: the fixed top-up's key (`top_up`), or
    the candidates; web hooks read that, never the name."""
    name = candidates_name(candidates, language)
    bought = {TOP_UP_FLAG: top_up} if top_up else {CUSTOM_TOP_UP_FLAG: str(candidates)}

    return {
        "name": name,
        "description": name,
        "product_id": settings.paddle_product_candidates,
        "unit_price": {"amount": str(candidates * cents), "currency_code": currency},
        "tax_mode": "external",
        "quantity": {"minimum": 1, "maximum": 1},
        "custom_data": bought,
    }


def paid_for(index: int, item: dict, data: dict) -> int:
    """What a line of a paid transaction cost before tax, in the transaction's currency (minor
    units), as Paddle charged it."""
    lines = data.get("details", {}).get("line_items", [])
    line = next((line for line in lines if line.get("price_id") == item["price"]["id"]), None)

    if line is None and index < len(lines):
        line = lines[index]

    return int(line["totals"]["subtotal"]) if line else 0


def bought(index: int, item: dict, data: dict) -> tuple[str, int, int] | None:
    """What a line of a paid transaction bought (a price billing made under its Paddle product):
    its key, what it was paid and the credits of its candidates, the same whatever the currency;
    None for anything else, or a count billing doesn't sell."""
    price = item["price"]
    product = settings.paddle_product_candidates
    found = price.get("custom_data") or {}

    if not product or price.get("product_id") != product:
        return None

    top_up = next((top_up for top_up in TOP_UPS if top_up.key == found.get(TOP_UP_FLAG)), None)
    count = str(found.get(CUSTOM_TOP_UP_FLAG, ""))

    if top_up is not None:
        key, candidates = top_up.key, top_up.candidates
    elif (
        count.isdigit()
        and candidate_tiers(DEFAULT_CURRENCY)[0][0] <= int(count) <= CUSTOM_TOP_UP_MAX
    ):
        key, candidates = CUSTOM_TOP_UP_KEY, int(count)
    else:
        return None

    return (
        key,
        paid_for(index, item, data),
        candidates * CANDIDATE_CREDITS * item.get("quantity", 1),
    )
