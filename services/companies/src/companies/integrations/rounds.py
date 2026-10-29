from datetime import timedelta
from uuid import UUID

import httpx
from prepza_common.http import http
from prepza_common.http.http import bearer

from companies.config import settings
from companies.core.security import service_token


async def create_sessions(payload: dict) -> list[dict]:
    response = await http.get_client().post(
        f"{settings.rounds_url}/internal/sessions",
        json=payload,
        headers=bearer(service_token("rounds")),
        timeout=60,
    )

    response.raise_for_status()

    return response.json()


async def invite_scores(invite_ids: list[UUID]) -> dict[str, dict]:
    if not invite_ids:
        return {}

    response = await http.get_client().post(
        f"{settings.rounds_url}/internal/invite-scores",
        json={"invite_ids": [str(invite_id) for invite_id in invite_ids]},
        headers=bearer(service_token("rounds")),
    )

    response.raise_for_status()

    return response.json()


async def answer_counts(set_ids: list[UUID]) -> dict[str, list[int]]:
    """Per interview set, its candidates' answers: [timed out, all]; sets without any are left
    out."""
    if not set_ids:
        return {}

    response = await http.get_client().post(
        f"{settings.rounds_url}/internal/answer-counts",
        json={"set_ids": [str(set_id) for set_id in set_ids]},
        headers=bearer(service_token("rounds")),
    )

    response.raise_for_status()

    return response.json()


async def scorecard(invite_id: UUID) -> list[dict] | None:
    response = await http.get_client().get(
        f"{settings.rounds_url}/internal/invites/{invite_id}/scorecard",
        headers=bearer(service_token("rounds")),
    )

    if response.status_code == httpx.codes.NOT_FOUND:
        return None

    response.raise_for_status()

    return response.json()


async def answer_patterns(invite_id: UUID) -> dict | None:
    """The integrity signals the candidate's answers and times show, and follow-up questions;
    None for a candidate without sections."""
    response = await http.get_client().get(
        f"{settings.rounds_url}/internal/invites/{invite_id}/answer-patterns",
        headers=bearer(service_token("rounds")),
    )

    if response.status_code == httpx.codes.NOT_FOUND:
        return None

    response.raise_for_status()

    return response.json()


async def delete_invite_sessions(invite_ids: list[UUID]) -> None:
    """Deletes these candidates' sessions, answers and signals; raises if rounds can't."""
    response = await http.get_client().post(
        f"{settings.rounds_url}/internal/invites/delete",
        json={"invite_ids": [str(invite_id) for invite_id in invite_ids]},
        headers=bearer(service_token("rounds")),
    )

    response.raise_for_status()


async def running_interviews() -> int:
    response = await http.get_client().get(
        f"{settings.rounds_url}/internal/maintenance/running",
        headers=bearer(service_token("rounds")),
    )

    response.raise_for_status()

    return response.json()["running"]


async def give_time_back(stopped: timedelta) -> None:
    response = await http.get_client().post(
        f"{settings.rounds_url}/internal/maintenance/resume",
        json={"seconds": stopped.total_seconds()},
        headers=bearer(service_token("rounds")),
    )

    response.raise_for_status()


async def fill_session_companies(companies: dict[UUID, UUID]) -> int:
    """Tells rounds each interview set's company, for its sections started before it kept it."""
    response = await http.get_client().post(
        f"{settings.rounds_url}/internal/session-companies",
        json={"companies": {str(key): str(value) for key, value in companies.items()}},
        headers=bearer(service_token("rounds")),
    )

    response.raise_for_status()

    return response.json()["filled"]
