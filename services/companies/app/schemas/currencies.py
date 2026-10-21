from pydantic import BaseModel, ConfigDict, Field

from app.constants.billing import CURRENCY_CODE


class CurrencyIn(BaseModel):
    # Billing refuses one it doesn't sell in.
    currency: str = Field(pattern=CURRENCY_CODE)


class CompanyCurrencyOut(BaseModel):
    """The currency the company pays in, automatic top-ups included."""

    currency: str
    # The ones it can choose.
    currencies: list[str]


class CatalogOut(BaseModel):
    """Billing's prices, as billing gives them, in `currency`."""

    model_config = ConfigDict(extra="allow")

    currency: str
