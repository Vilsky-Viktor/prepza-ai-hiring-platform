"""The daily candidate jobs start no batch JOB_RUN_SECONDS into their run, so a run ends within
the request's timeout however much is left; the next run goes on."""

import asyncio
import uuid
from types import SimpleNamespace

import pytest

from companies.constants.invites import JOB_RUN_SECONDS
from companies.integrations import billing, rounds
from companies.repositories import accounts, invite_expiry, invites, removals
from companies.services import candidate_billing, removal_replay, retention

# The clock the jobs read; each batch read takes JOB_RUN_SECONDS, so the first one uses up the
# run's time.
clock = [0]


async def nothing(session, *args):
    return None


def read_batch(rows: list) -> list:
    clock[0] += JOB_RUN_SECONDS

    return rows


def invite():
    return SimpleNamespace(id=uuid.uuid4(), interview_id=uuid.uuid4(), hold_key="key")


async def expired_invites(session, before, limit):
    return read_batch([(uuid.uuid4(), uuid.uuid4(), "ann@example.com", "invited", "key")])


async def expiring(session, before, limit):
    return read_batch([invite()])


async def restored(session, after, limit):
    return read_batch([(invite(), uuid.uuid4())])


async def no_leftovers(session, limit):
    return []


async def marked(session, invite_id, before):
    return True


@pytest.mark.parametrize(
    ("module", "job", "fakes"),
    [
        (
            retention,
            retention.delete_expired_candidates,
            {(accounts, "expired_invites"): expired_invites},
        ),
        (
            candidate_billing,
            candidate_billing.expire_unstarted,
            {(invite_expiry, "expiring"): expiring, (invite_expiry, "mark_expired"): marked},
        ),
        (
            removal_replay,
            removal_replay.replay,
            {
                (removals, "restored"): restored,
                (removals, "forget"): nothing,
                (accounts, "blanked_invites"): no_leftovers,
                (invites, "remove"): nothing,
            },
        ),
    ],
    ids=["retention", "expiry", "removals"],
)
def test_a_job_with_more_left_stops_at_its_time(monkeypatch, module, job, fakes):
    clock[0] = 0
    monkeypatch.setattr(module, "monotonic", lambda: clock[0])
    monkeypatch.setattr(rounds, "delete_invite_sessions", nothing)
    monkeypatch.setattr(billing, "release_candidate", nothing)
    monkeypatch.setattr(accounts, "delete_invites", nothing)

    for (owner, name), fake in fakes.items():
        monkeypatch.setattr(owner, name, fake)

    # The database never runs out, yet the run ends after its one batch.
    assert asyncio.run(job()) == 1
