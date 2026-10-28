import pytest

from billing.repositories import stats


def test_superadmin_gets_the_counts_of_the_month_asked(client, monkeypatch, signed_in):
    asked = []

    async def counts(session, period):
        asked.append(period)

        return {"top_ups": 3}, {"USD": 5_000, "EUR": 4_000, "GBP": 0}

    monkeypatch.setattr(stats, "stats", counts)
    signed_in("ann@example.com")

    body = client.get("/superadmin/stats?period=2026-10").json()

    assert asked == ["2026-10"]
    assert body["counts"] == {"top_ups": 3}
    # What top-ups paid, in each currency apart.
    assert body["paid"] == {"USD": 5_000, "EUR": 4_000, "GBP": 0}


def test_without_a_month_the_counts_are_all_time(client, monkeypatch, signed_in):
    asked = []

    async def counts(session, period):
        asked.append(period)

        return {}, {}

    monkeypatch.setattr(stats, "stats", counts)
    signed_in("ann@example.com")

    assert client.get("/superadmin/stats").status_code == 200
    assert asked == [None]


def test_a_year_is_a_period_too(client, monkeypatch, signed_in):
    asked = []

    async def counts(session, period):
        asked.append(period)

        return {}, {}

    monkeypatch.setattr(stats, "stats", counts)
    signed_in("ann@example.com")

    assert client.get("/superadmin/stats?period=2026").status_code == 200
    assert asked == ["2026"]


@pytest.mark.parametrize("period", ["2026-13", "2026-1", "october", "26"])
def test_a_period_that_isnt_one_is_refused(client, signed_in, period):
    signed_in("ann@example.com")

    assert client.get(f"/superadmin/stats?period={period}").status_code == 422


def test_stats_are_not_found_for_others(client, signed_in):
    signed_in("eve@example.com")

    assert client.get("/superadmin/stats?period=2026-10").status_code == 404
