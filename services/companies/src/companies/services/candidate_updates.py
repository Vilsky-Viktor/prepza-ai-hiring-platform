from datetime import datetime

from prepza_common.config.constants import MAX_UPDATES

from companies.core.db import Session
from companies.helpers.candidate_updates import candidate_updates, update_counts
from companies.repositories import candidate_updates as updates_storage
from companies.schemas.candidate_updates import CandidateUpdatesOut


async def updates(company_ids: list, since: datetime, until: datetime) -> CandidateUpdatesOut:
    """Each candidate of these companies who started, finished or whose invite wasn't delivered
    after `since` and up to `until`: the newest MAX_UPDATES, newest first, and the counts of
    all."""
    window = (company_ids, since, until)

    async with Session() as session:
        rows = await updates_storage.changed(session, *window, MAX_UPDATES)
        counts = await updates_storage.counts(session, *window)

    items = candidate_updates(rows, since, until)[:MAX_UPDATES]

    return CandidateUpdatesOut(items=items, counts=update_counts(*counts))
