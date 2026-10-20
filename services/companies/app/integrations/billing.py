import asyncio
from uuid import UUID

import httpx
from fastapi import HTTPException, status
from prepza_common import http
from prepza_common.backoff import wait_seconds
from prepza_common.http import bearer, passed_on

from app.config.settings import settings
from app.constants.billing import (
    PAYMENT_FAILURE_TIMEOUT_SECONDS,
    WELCOME_ATTEMPTS,
    WELCOME_FIRST_WAIT_SECONDS,
)
from app.service_auth import service_token


def _headers() -> dict:
    return bearer(service_token("billing"))


async def hold_candidate(company_id: UUID, key: str) -> None:
    """Sets a candidate's credits aside. Billing's 402 and its message reach the user unchanged."""
    response = await http.get_client().post(
        f"{settings.billing_url}/internal/candidates/hold",
        params={"company_id": str(company_id), "key": key},
        headers=_headers(),
    )

    if response.status_code == status.HTTP_402_PAYMENT_REQUIRED:
        raise HTTPException(status.HTTP_402_PAYMENT_REQUIRED, response.json()["detail"])

    response.raise_for_status()


async def charge_candidate(key: str) -> None:
    response = await http.get_client().post(
        f"{settings.billing_url}/internal/candidates/charge",
        params={"key": key},
        headers=_headers(),
    )

    response.raise_for_status()


async def release_candidate(key: str) -> None:
    response = await http.get_client().post(
        f"{settings.billing_url}/internal/candidates/release",
        params={"key": key},
        headers=_headers(),
    )

    response.raise_for_status()


async def welcome_company(
    company_id: UUID, owner_email: str, referral: str | None, related: list[str]
) -> None:
    """The welcome credits come once per owner's email; billing keeps only a hash of it. A
    referral code counts unless it's from one of the owner's other companies (`related`).
    Billing gives it once per company, so a failed try is repeated: its answer may have been
    lost after the gift was given."""
    for attempt in range(WELCOME_ATTEMPTS):
        try:
            response = await http.get_client().post(
                f"{settings.billing_url}/internal/companies/{company_id}/welcome",
                json={"owner_email": owner_email, "referral": referral, "related": related},
                headers=_headers(),
            )
            response.raise_for_status()

            return
        except Exception:
            if attempt == WELCOME_ATTEMPTS - 1:
                raise

            await asyncio.sleep(wait_seconds(WELCOME_FIRST_WAIT_SECONDS, attempt))


async def company_referral(company_id: UUID) -> dict:
    """The company's referral code, its reward, and how many it has earned for."""
    response = await http.get_client().get(
        f"{settings.billing_url}/internal/companies/{company_id}/referral",
        headers=_headers(),
    )

    response.raise_for_status()

    return response.json()


async def company_paid(company_id: UUID) -> bool:
    """Whether the company ever topped up. When billing can't say, it counts as not: the
    company is then held to the daily limit for everyone, rather than refused."""
    try:
        response = await http.get_client().get(
            f"{settings.billing_url}/internal/companies/{company_id}/paid",
            headers=_headers(),
        )
        response.raise_for_status()
    except httpx.HTTPError:
        return False

    return response.json()["paid"]


async def company_credits(company_id: UUID) -> dict:
    """The company's available credits, and whether they're running low."""
    response = await http.get_client().get(
        f"{settings.billing_url}/internal/companies/{company_id}/credits",
        headers=_headers(),
    )

    response.raise_for_status()

    return response.json()


async def delete_company(company_id: UUID) -> None:
    """The company's wallet and history; safe to repeat."""
    response = await http.get_client().delete(
        f"{settings.billing_url}/internal/companies/{company_id}",
        headers=_headers(),
    )

    response.raise_for_status()


async def companies_credits(company_ids: list[UUID]) -> dict[str, dict]:
    """Each company's balance, by id."""
    response = await http.get_client().post(
        f"{settings.billing_url}/internal/companies/credits",
        json={"owner_ids": [str(company_id) for company_id in company_ids]},
        headers=_headers(),
    )

    response.raise_for_status()

    return response.json()


def _auto_top_up_url(company_id: UUID) -> str:
    return f"{settings.billing_url}/internal/companies/{company_id}/auto-top-up"


async def auto_top_up(company_id: UUID) -> dict:
    """The company's automatic top-up and its choices."""
    response = await http.get_client().get(_auto_top_up_url(company_id), headers=_headers())

    response.raise_for_status()

    return response.json()


async def turn_on_auto_top_up(company_id: UUID, body: dict, buyer_id: str) -> dict:
    """Saves the choice; billing's answer carries the checkout when the card isn't saved yet.
    Its refusals reach the user unchanged: a choice it doesn't offer (422), or a running one
    paid by someone else's card (403)."""
    response = await http.get_client().put(
        _auto_top_up_url(company_id),
        json=body,
        params={"buyer_id": buyer_id},
        headers=_headers(),
    )

    refusals = {status.HTTP_403_FORBIDDEN, status.HTTP_422_UNPROCESSABLE_CONTENT}

    return passed_on(response, refusals).json()


async def turn_off_auto_top_up(company_id: UUID, buyer_id: str | None = None) -> None:
    """With `buyer_id`, off only when that person's card pays for it."""
    params = {"buyer_id": buyer_id} if buyer_id else None
    response = await http.get_client().delete(
        _auto_top_up_url(company_id), params=params, headers=_headers()
    )

    response.raise_for_status()


async def company_history(company_id: UUID, offset: int, limit: int) -> list[dict]:
    """A page of the company's credit movements, newest first."""
    response = await http.get_client().get(
        f"{settings.billing_url}/internal/companies/{company_id}/history",
        params={"offset": offset, "limit": limit},
        headers=_headers(),
    )

    response.raise_for_status()

    return response.json()


async def company_invoice(company_id: UUID, transaction_id: str) -> str:
    """A temporary link to the invoice of one of the company's top-ups; billing's 404 for any
    other transaction reaches the user unchanged."""
    response = await http.get_client().get(
        f"{settings.billing_url}/internal/companies/{company_id}/invoice",
        params={"transaction_id": transaction_id},
        headers=_headers(),
    )

    if response.status_code == status.HTTP_404_NOT_FOUND:
        raise HTTPException(status.HTTP_404_NOT_FOUND, response.json()["detail"])

    response.raise_for_status()

    return response.json()["url"]


async def company_checkout(company_id: UUID, candidates: int, buyer_id: str) -> str:
    """The Paddle transaction of a checkout for a top-up of `candidates` into the company, made
    by billing; its refusal of a count or a price it doesn't sell (422) reaches the user
    unchanged."""
    response = await http.get_client().post(
        f"{settings.billing_url}/internal/companies/{company_id}/checkout",
        params={"buyer_id": buyer_id},
        json={"candidates": candidates},
        headers=_headers(),
    )

    return passed_on(response, {status.HTTP_422_UNPROCESSABLE_CONTENT}).json()["transaction_id"]


async def company_payment_failure(company_id: UUID, transaction_id: str, buyer_id: str) -> str:
    """Why the latest payment of the buyer's checkout into the company failed; billing's 404 for
    a transaction that isn't theirs, and its 422 for an id that isn't a transaction's, reach the
    user unchanged."""
    response = await http.get_client().get(
        f"{settings.billing_url}/internal/companies/{company_id}/payment-failure",
        params={"transaction_id": transaction_id, "buyer_id": buyer_id},
        headers=_headers(),
        timeout=PAYMENT_FAILURE_TIMEOUT_SECONDS,
    )
    refusals = {status.HTTP_404_NOT_FOUND, status.HTTP_422_UNPROCESSABLE_CONTENT}

    return passed_on(response, refusals).json()["reason"]


async def purchase_owner(transaction_id: str) -> dict | None:
    """Whose wallet a top-up's Paddle transaction paid into (`owner_type`, `owner_id`); None
    when no top-up has it."""
    response = await http.get_client().get(
        f"{settings.billing_url}/internal/purchases/{transaction_id}",
        headers=_headers(),
    )

    if response.status_code == status.HTTP_404_NOT_FOUND:
        return None

    response.raise_for_status()

    return response.json()


async def buyer_purchases(user_id: str) -> list[dict]:
    """The company top-ups the user paid for, one per transaction, newest first (at most
    billing's limit): {"transaction_id", "company_id", "total", "currency", "created_at"}."""
    response = await http.get_client().get(
        f"{settings.billing_url}/internal/purchases",
        params={"buyer_id": user_id},
        headers=_headers(),
    )

    response.raise_for_status()

    return response.json()


async def candidate_hold(key: str) -> str | None:
    """Whether the credits of the invite with that key are open, charged or released; None
    when none were held."""
    response = await http.get_client().get(
        f"{settings.billing_url}/internal/candidates/hold",
        params={"key": key},
        headers=_headers(),
    )

    if response.status_code == status.HTTP_404_NOT_FOUND:
        return None

    response.raise_for_status()

    return response.json()["status"]


async def adjust_company(company_id: UUID, amount: int, note: str, key: UUID) -> None:
    """A superadmin's adjustment of the company's credits, once per key. Billing's refusals
    reach the superadmin unchanged: one that would take the available balance below zero (409),
    or an amount of zero (422)."""
    response = await http.get_client().post(
        f"{settings.billing_url}/internal/companies/{company_id}/adjustments",
        json={"amount": amount, "note": note, "key": str(key)},
        headers=_headers(),
    )

    passed_on(response, {status.HTTP_409_CONFLICT, status.HTTP_422_UNPROCESSABLE_CONTENT})
