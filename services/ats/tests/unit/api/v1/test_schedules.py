from datetime import UTC, datetime, timedelta

from ats.repositories import ats_candidates as candidates_storage
from ats.services import outbox as outbox_service
from ats.services import recovery


def test_the_outbox_schedule_publishes_waiting_events(client, monkeypatch):
    flushed = []

    async def flush():
        flushed.append(True)

        return 0

    monkeypatch.setattr(outbox_service, "flush", flush)

    assert client.post("/internal/schedules/outbox").status_code == 204
    assert flushed == [True]


def test_the_daily_job_starts_cut_off_invites_again_and_deletes_old_candidates(client, monkeypatch):
    done = []

    async def recover():
        done.append("recover")

        return 2

    async def delete_older_than(session, before):
        done.append(before)

        return 3

    monkeypatch.setattr(recovery, "recover", recover)
    monkeypatch.setattr(candidates_storage, "delete_older_than", delete_older_than)

    assert client.post("/internal/schedules/recover").status_code == 204
    assert done[0] == "recover"
    expected = datetime.now(UTC) - timedelta(days=365)
    assert abs(done[1] - expected) < timedelta(minutes=1)
