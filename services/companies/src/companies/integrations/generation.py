from uuid import UUID

import httpx
from testee_common.http import http
from testee_common.http.http import bearer

from companies.config import settings
from companies.constants.generation import REGENERATE_CALL_SECONDS
from companies.core.security import service_token


async def create(
    text: str,
    company_id: UUID,
    owner_uid: str,
    language: str,
    generate_in: str | None,
    paid: bool,
) -> dict:
    """Only companies may start an interview generation, after checking the user's membership."""
    response = await http.get_client().post(
        f"{settings.generation_url}/internal/generations",
        json={
            "text": text,
            "company_id": str(company_id),
            "owner_uid": owner_uid,
            "language": language,
            "generate_in": generate_in,
            "paid": paid,
        },
        headers=bearer(service_token("generation")),
    )

    response.raise_for_status()

    return response.json()


async def regenerate_question(
    question_id: UUID, set_id: UUID, user_id: str, paid: bool
) -> httpx.Response:
    """The raw response, so the caller can pass rate limits and failures through."""
    return await http.get_client().post(
        f"{settings.generation_url}/internal/questions/{question_id}/regenerate",
        json={"user_id": user_id, "set_id": str(set_id), "paid": paid},
        headers=bearer(service_token("generation")),
        timeout=REGENERATE_CALL_SECONDS,
    )


async def get(generation_id: UUID, company_id: UUID) -> dict | None:
    """Any member can see the company's generations, not only the admin who started one."""
    response = await http.get_client().get(
        f"{settings.generation_url}/internal/generations/{generation_id}",
        params={"company_id": str(company_id)},
        headers=bearer(service_token("generation")),
    )

    if response.status_code == httpx.codes.NOT_FOUND:
        return None

    response.raise_for_status()

    return response.json()


async def review(generation_id: UUID, company_id: UUID, body: dict) -> httpx.Response:
    """The raw response, so the caller can pass a 409 (already reviewed) through."""
    return await http.get_client().post(
        f"{settings.generation_url}/internal/generations/{generation_id}/review",
        params={"company_id": str(company_id)},
        json=body,
        headers=bearer(service_token("generation")),
    )


async def cancel(generation_id: UUID, company_id: UUID) -> httpx.Response:
    """The raw response, so the caller can pass a 409 (already finished) through."""
    return await http.get_client().post(
        f"{settings.generation_url}/internal/generations/{generation_id}/cancel",
        params={"company_id": str(company_id)},
        headers=bearer(service_token("generation")),
    )


async def retry(generation_id: UUID, company_id: UUID) -> httpx.Response:
    """The raw response, so the caller can pass a 409 (not failed) through."""
    return await http.get_client().post(
        f"{settings.generation_url}/internal/generations/{generation_id}/retry",
        params={"company_id": str(company_id)},
        headers=bearer(service_token("generation")),
    )
