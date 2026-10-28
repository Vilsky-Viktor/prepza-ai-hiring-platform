"""Two interviews made at once can't both take a company's last place without candidates."""

import os
import uuid

from prepza_common.db.lock_waits import hold_first_commit, race

from companies.core.exceptions import OverLimit
from companies.repositories import companies, interviews


def test_two_interviews_at_once_cant_both_take_the_last_place(run, monkeypatch):
    async def scenario():
        company = await companies.create(f"Quota {uuid.uuid4()}", "owner", "o@example.com")
        # The second waits on the company's interview lock until the first commits.
        held = hold_first_commit(monkeypatch, interviews)
        made = await race(
            os.environ["DATABASE_URL"],
            held,
            *(interviews.create(company.id, uuid.uuid4(), "en", 60, most=1) for _ in range(2)),
        )

        return [type(item).__name__ for item in made]

    assert run(scenario()) == ["Interview", OverLimit.__name__]
