"""Deletions too big for one transaction: a batch at a time, each its own, so a deletion cut off
midway goes on when run again."""

from testee_common.config.constants import DELETE_BATCH

from companies.core.db import Session
from companies.repositories import batch_deletion


async def delete_invites(*conditions) -> list[tuple]:
    """Deletes the invites matching `conditions`, each batch with guests.deleted for its guests.
    Returns (interview id, email, status, hold key) of those not finished."""
    unfinished = []

    while True:
        async with Session.begin() as session:
            count, rows = await batch_deletion.delete_invites_batch(session, *conditions)

        unfinished += rows

        if count < DELETE_BATCH:
            return unfinished


async def delete_interviews(company_id) -> None:
    """Deletes the company's interviews; an invite made meanwhile goes with its interview
    (cascade), its guest announced."""
    while True:
        async with Session.begin() as session:
            count = await batch_deletion.delete_interviews_batch(session, company_id)

        if count < DELETE_BATCH:
            return
