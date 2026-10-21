"""Two interviews made at once can't both take a company's last place without candidates."""

import asyncio
import uuid

from app.core.exceptions import OverLimit
from app.storage import companies, interviews


def test_two_interviews_at_once_cant_both_take_the_last_place(run):
    async def scenario():
        company = await companies.create(f"Quota {uuid.uuid4()}", "owner", "o@example.com")
        made = await asyncio.gather(
            *(interviews.create(company.id, uuid.uuid4(), "en", 60, most=1) for _ in range(2)),
            return_exceptions=True,
        )

        return sorted(type(item).__name__ for item in made)

    assert run(scenario()) == sorted(["Interview", OverLimit.__name__])
