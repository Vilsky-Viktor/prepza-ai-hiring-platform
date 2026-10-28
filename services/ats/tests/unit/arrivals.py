"""Pub/Sub, faked for ATS web hooks: the ats.candidate_arrived event of each candidate a web hook
saved is delivered once the request flushes its outbox, and invites them as invite_arrived does."""

from ats.repositories import ats_candidates
from ats.services import ats_candidates as flow


def deliver_arrivals(monkeypatch, rows: dict, then=None, connection=None) -> None:
    """`rows`: the fixture's saved candidates, by their ATS id; `then`: the fixture's own flush,
    still called; `connection`: the one every candidate came through, when the fixture doesn't
    look connections up itself."""
    delivered = set()

    async def get(session, row_id):
        return next((row for row in rows.values() if row.id == row_id), None)

    async def flush():
        for row in list(rows.values()):
            if row.id not in delivered:
                delivered.add(row.id)
                await flow.invite_arrived({"ats_candidate_id": str(row.id)})

        if then is not None:
            await then()

    async def connection_by_id(session, connection_id):
        return connection

    if connection is not None:
        monkeypatch.setattr(flow.ats, "connection_by_id", connection_by_id)

    monkeypatch.setattr(ats_candidates, "get", get)
    monkeypatch.setattr(flow.outbox_service, "flush_quietly", flush)
