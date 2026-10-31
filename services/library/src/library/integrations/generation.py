from uuid import UUID

from testee_common.http import http
from testee_common.http.http import bearer

from library.config import settings
from library.core.security import service_token


async def verify_question(question_id: UUID, flag: str, now: bool = False) -> None:
    """Queues the verifier for a newly flagged question; raises if generation can't."""
    response = await http.get_client().post(
        f"{settings.generation_url}/internal/questions/{question_id}/verify",
        json={"flag": flag, "now": now},
        headers=bearer(service_token("generation")),
    )

    response.raise_for_status()
