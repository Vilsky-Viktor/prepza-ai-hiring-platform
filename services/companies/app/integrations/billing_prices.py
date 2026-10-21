"""Billing's prices for a company, in the currency it pays in, and what's bought with them: its
catalog and currency, a top-up's checkout and the automatic top-up. `country` is the visitor's
(VisitorCountry), which billing goes by for a company with no currency saved yet."""

from uuid import UUID

from fastapi import status
from prepza_common import http
from prepza_common.http import bearer, passed_on

from app.config.settings import settings
from app.service_auth import service_token


def _headers() -> dict:
    return bearer(service_token("billing"))


def _company(company_id: UUID, path: str) -> str:
    return f"{settings.billing_url}/internal/companies/{company_id}/{path}"


def _country(country: str | None) -> dict:
    return {"country": country} if country else {}


async def catalog(company_id: UUID, country: str | None) -> dict:
    """Every price, in the company's currency."""
    response = await http.get_client().get(
        _company(company_id, "catalog"), params=_country(country), headers=_headers()
    )

    response.raise_for_status()

    return response.json()


async def currency(company_id: UUID, country: str | None) -> dict:
    """The company's currency, and the ones it can choose."""
    response = await http.get_client().get(
        _company(company_id, "currency"), params=_country(country), headers=_headers()
    )

    response.raise_for_status()

    return response.json()


async def choose_currency(company_id: UUID, chosen: str) -> dict:
    """Billing's refusal of a currency it doesn't sell in (422) reaches the user unchanged."""
    response = await http.get_client().put(
        _company(company_id, "currency"), json={"currency": chosen}, headers=_headers()
    )

    return passed_on(response, {status.HTTP_422_UNPROCESSABLE_CONTENT}).json()


async def auto_top_up(company_id: UUID, country: str | None = None) -> dict:
    """The company's automatic top-up and its choices, priced in its currency."""
    response = await http.get_client().get(
        _company(company_id, "auto-top-up"), params=_country(country), headers=_headers()
    )

    response.raise_for_status()

    return response.json()


async def turn_on_auto_top_up(
    company_id: UUID, body: dict, buyer_id: str, country: str | None
) -> dict:
    """Saves the choice; billing's answer carries the checkout when the card isn't saved yet.
    Its refusals reach the user unchanged: a choice it doesn't offer (422), or a running one
    paid by someone else's card (403)."""
    response = await http.get_client().put(
        _company(company_id, "auto-top-up"),
        json=body,
        params={"buyer_id": buyer_id, **_country(country)},
        headers=_headers(),
    )

    refusals = {status.HTTP_403_FORBIDDEN, status.HTTP_422_UNPROCESSABLE_CONTENT}

    return passed_on(response, refusals).json()


async def turn_off_auto_top_up(company_id: UUID, buyer_id: str | None = None) -> None:
    """With `buyer_id`, off only when that person's card pays for it."""
    params = {"buyer_id": buyer_id} if buyer_id else None
    response = await http.get_client().delete(
        _company(company_id, "auto-top-up"), params=params, headers=_headers()
    )

    response.raise_for_status()


async def update_auto_top_up_card(company_id: UUID, buyer_id: str) -> str:
    """The Paddle transaction of the checkout that saves a new card for the running automatic
    top-up. Billing's refusals reach the user unchanged: someone else's card pays for it (403),
    or it isn't running (409)."""
    response = await http.get_client().post(
        _company(company_id, "auto-top-up/card"),
        params={"buyer_id": buyer_id},
        headers=_headers(),
    )
    refusals = {status.HTTP_403_FORBIDDEN, status.HTTP_409_CONFLICT}

    return passed_on(response, refusals).json()["transaction_id"]


async def company_checkout(
    company_id: UUID, candidates: int, buyer_id: str, country: str | None
) -> str:
    """The Paddle transaction of a checkout for a top-up of `candidates` into the company, made
    by billing in the company's currency; its refusal of a count or a price it doesn't sell
    (422) reaches the user unchanged."""
    response = await http.get_client().post(
        _company(company_id, "checkout"),
        params={"buyer_id": buyer_id, **_country(country)},
        json={"candidates": candidates},
        headers=_headers(),
    )

    return passed_on(response, {status.HTTP_422_UNPROCESSABLE_CONTENT}).json()["transaction_id"]
