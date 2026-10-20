from app.config.settings import settings
from app.constants.credits import CANDIDATE_CREDITS
from app.constants.products import CURRENCY, CUSTOM_TOP_UP_FLAG, CUSTOM_TOP_UP_KEY, TOP_UPS
from app.helpers.credits import credits_for, custom_top_up


def price_ids() -> dict[str, str]:
    """Paddle's price id of each top-up; one without an id isn't sold."""
    return {product.key: getattr(settings, f"paddle_price_{product.key}") for product in TOP_UPS}


def bought_for(price_id: str, quantity: int) -> tuple[str, int, int] | None:
    """What a line of a paid transaction bought with one of the fixed top-ups' prices: its key,
    what it was paid (cents) and the credits it buys; None if it isn't one of them."""
    by_price = {price: key for key, price in price_ids().items() if price}
    product = next((item for item in TOP_UPS if item.key == by_price.get(price_id)), None)

    if product is None:
        return None

    paid = product.price_cents * quantity

    return product.key, paid, credits_for(paid)


def candidates_price(candidates: int, cents: int) -> dict:
    """Paddle's price, made in the transaction itself, of a top-up of `candidates` at `cents`
    each: one item the buyer can't change, its tax added on top, as the fixed top-ups'."""
    name = f"{candidates:,} candidates"

    return {
        "name": name,
        "description": name,
        "product_id": settings.paddle_product_candidates,
        "unit_price": {"amount": str(candidates * cents), "currency_code": CURRENCY},
        "tax_mode": "external",
        "quantity": {"minimum": 1, "maximum": 1},
    }


def custom_bought(item: dict, custom_data: dict) -> tuple[str, int, int] | None:
    """What a line of a paid transaction bought as a top-up of any number of candidates (Paddle's
    product for it): its key, what it was paid (cents) and the credits of the candidates billing
    put in the transaction's custom data, a count it sells; None otherwise."""
    price = item["price"]
    candidates = str(custom_data.get(CUSTOM_TOP_UP_FLAG, ""))
    product = settings.paddle_product_candidates

    if not product or price.get("product_id") != product or not candidates.isdigit():
        return None

    count = int(candidates)
    sold = custom_top_up(count)

    if sold is None or sold[0] != count:
        return None

    return CUSTOM_TOP_UP_KEY, int(price["unit_price"]["amount"]), count * CANDIDATE_CREDITS
