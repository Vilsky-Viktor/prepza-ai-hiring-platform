from datetime import timedelta

from rounds.core.db import Session
from rounds.repositories import running


async def give_time_back(stopped: timedelta) -> None:
    """Running interviews get back the time maintenance mode was on: every section's start and
    the question on screen's, in one save."""
    async with Session.begin() as session:
        await running.give_time_back(session, stopped)
