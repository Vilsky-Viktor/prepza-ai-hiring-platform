"""Candidates' credit keys: both services' copies are keyed alike (testee_common.limits.credit_keys)."""

from testee_common.limits.credit_keys import rekeyed

PLAIN = "1b4e28ba-2fa1-11d2-883f-0016d3cca427:0f1e2d3c4b5a69788796a5b4c3d2e1f0"


def test_a_keys_hash_is_keyed_and_keeps_its_interview_and_length():
    new = rekeyed(PLAIN, "key-1")

    assert new.startswith("1b4e28ba-2fa1-11d2-883f-0016d3cca427:")
    assert new != PLAIN and len(new) == len(PLAIN)
    assert new == rekeyed(PLAIN, "key-1") != rekeyed(PLAIN, "key-2")
