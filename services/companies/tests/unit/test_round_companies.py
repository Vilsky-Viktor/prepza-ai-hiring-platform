import asyncio
import uuid

from app.services import round_companies


def test_every_interviews_company_goes_to_rounds_a_batch_at_a_time(monkeypatch):
    monkeypatch.setattr(round_companies, "READ_BATCH", 2)
    rows = sorted((uuid.uuid4(), uuid.uuid4(), uuid.uuid4()) for _ in range(3))
    sent = []

    async def set_companies(after, limit):
        later = [row for row in rows if after is None or row[0] > after]

        return later[:limit]

    async def fill(companies):
        sent.append(companies)

        return len(companies)

    monkeypatch.setattr(round_companies.interviews, "set_companies", set_companies)
    monkeypatch.setattr(round_companies.rounds, "fill_session_companies", fill)

    assert asyncio.run(round_companies.backfill()) == 3
    assert sent == [
        {set_id: company for _, set_id, company in rows[:2]},
        {set_id: company for _, set_id, company in rows[2:]},
    ]
