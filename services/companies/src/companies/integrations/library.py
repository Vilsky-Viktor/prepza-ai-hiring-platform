from uuid import UUID

import httpx
from prepza_common.db.paging import Page
from prepza_common.http import http
from prepza_common.http.http import bearer

from companies.config import settings
from companies.constants.superadmin import ACCOUNT_ID
from companies.core.security import service_token


async def copy_template(template_id: UUID, company_id: UUID) -> dict | None:
    """The company's own test set made from a template: {"id", "title", "language", "level"},
    or None when there's no such template."""
    response = await http.get_client().post(
        f"{settings.library_url}/internal/templates/{template_id}/copy",
        json={"company_id": str(company_id)},
        headers=bearer(service_token("library")),
    )

    if response.status_code == httpx.codes.NOT_FOUND:
        return None

    response.raise_for_status()

    return response.json()


async def get_set(set_id: UUID) -> dict | None:
    response = await http.get_client().get(
        f"{settings.library_url}/internal/sets/{set_id}",
        headers=bearer(service_token("library")),
    )

    if response.status_code == httpx.codes.NOT_FOUND:
        return None

    response.raise_for_status()

    return response.json()


async def rename_set(set_id: UUID, title: str) -> None:
    response = await http.get_client().patch(
        f"{settings.library_url}/internal/sets/{set_id}/title",
        json={"title": title},
        headers=bearer(service_token("library")),
    )

    response.raise_for_status()


async def get_topic_questions(set_id: UUID, topic_id: UUID) -> list[dict] | None:
    response = await http.get_client().get(
        f"{settings.library_url}/internal/sets/{set_id}/topics/{topic_id}/questions",
        headers=bearer(service_token("library")),
    )

    if response.status_code == httpx.codes.NOT_FOUND:
        return None

    response.raise_for_status()

    return response.json()


async def get_question_reports(set_id: UUID, question_id: UUID, page: Page) -> list[dict] | None:
    response = await http.get_client().get(
        f"{settings.library_url}/internal/sets/{set_id}/questions/{question_id}/reports",
        params={"offset": page.offset, "limit": page.limit},
        headers=bearer(service_token("library")),
    )

    if response.status_code == httpx.codes.NOT_FOUND:
        return None

    response.raise_for_status()

    return response.json()


async def get_content(set_id: UUID) -> dict | None:
    response = await http.get_client().get(
        f"{settings.library_url}/internal/sets/{set_id}/content",
        headers=bearer(service_token("library")),
    )

    if response.status_code == httpx.codes.NOT_FOUND:
        return None

    response.raise_for_status()

    return response.json()


async def mark_wrong(question_id: UUID) -> None:
    response = await http.get_client().post(
        f"{settings.library_url}/internal/questions/{question_id}/wrong",
        headers=bearer(service_token("library")),
    )

    response.raise_for_status()


async def get_question_context(question_id: UUID) -> dict | None:
    """The question's set and topic: {"set_id", ...}, or None when there's no such question."""
    response = await http.get_client().get(
        f"{settings.library_url}/internal/questions/{question_id}/context",
        headers=bearer(service_token("library")),
    )

    if response.status_code == httpx.codes.NOT_FOUND:
        return None

    response.raise_for_status()

    return response.json()


async def account(user_id: str) -> dict | None:
    """The account with that id ({"user_id", "email", "created_at"}); None when there's none, or
    the text couldn't be an account's id."""
    if not ACCOUNT_ID.fullmatch(user_id):
        return None

    response = await http.get_client().get(
        f"{settings.library_url}/internal/accounts/{user_id}",
        headers=bearer(service_token("library")),
    )

    if response.status_code == httpx.codes.NOT_FOUND:
        return None

    response.raise_for_status()

    return response.json()


async def account_by_email(email: str) -> dict | None:
    """The account signed in with the address, as account() gives it; None when there's none.
    The address goes in the body, which request logs don't record."""
    response = await http.get_client().post(
        f"{settings.library_url}/internal/accounts/lookup",
        json={"email": email},
        headers=bearer(service_token("library")),
    )

    if response.status_code == httpx.codes.NOT_FOUND:
        return None

    response.raise_for_status()

    return response.json()
