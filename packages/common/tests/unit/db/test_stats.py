from datetime import UTC, datetime

from prepza_common.db.stats import period_range


def test_a_month_runs_to_the_start_of_the_next():
    assert period_range("2026-02") == (
        datetime(2026, 2, 1, tzinfo=UTC),
        datetime(2026, 3, 1, tzinfo=UTC),
    )


def test_december_runs_into_the_new_year():
    assert period_range("2025-12")[1] == datetime(2026, 1, 1, tzinfo=UTC)


def test_a_year_runs_from_january_to_the_next_january():
    assert period_range("2026") == (
        datetime(2026, 1, 1, tzinfo=UTC),
        datetime(2027, 1, 1, tzinfo=UTC),
    )
