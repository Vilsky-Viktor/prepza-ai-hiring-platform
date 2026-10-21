from prepza_common.money import money


def test_whole_yen_and_won_are_written_as_paddle_counts_them():
    """Yen and won have no smaller unit: billing's 750 is ¥750, not ¥7.50."""
    assert money(750, "JPY", "en") == "¥750"
    assert money(1_375_000, "KRW", "en") == "₩1,375,000"
    assert money(260, "CHF", "en") == "CHF\u00a02.60"
