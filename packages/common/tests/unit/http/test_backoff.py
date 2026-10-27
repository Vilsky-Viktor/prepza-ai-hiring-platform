from prepza_common.http.backoff import wait_seconds


def test_waits_grow_and_are_spread_out():
    waits = [wait_seconds(1, 3) for _ in range(200)]

    assert all(0 <= wait <= 8 for wait in waits)
    # Spread out, not all the same moment.
    assert len(set(waits)) > 100
    assert max(wait_seconds(1, 0) for _ in range(200)) <= 1
