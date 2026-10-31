import hashlib
import hmac
import json
from datetime import UTC, datetime

import pytest
from testee_common.auth.tokens import hashed

from api.helpers.keys import add_months, expired, new_key
from api.helpers.webhooks import body_of, masked, signature


def test_a_new_key_is_kept_only_as_its_hash():
    key, shown, stored = new_key()

    assert key.startswith("te_") and len(key) > 30
    assert key.startswith(shown) and len(shown) == 10
    assert stored == hashlib.sha256(key.encode()).hexdigest() == hashed(key)
    assert new_key()[0] != key


def test_a_key_expires_at_its_time_and_one_without_never_does():
    now = datetime(2026, 10, 8, tzinfo=UTC)

    assert not expired(None, now)
    assert not expired(datetime(2026, 10, 9, tzinfo=UTC), now)
    assert expired(now, now)


@pytest.mark.parametrize(
    ("start", "months", "end"),
    [
        (datetime(2026, 10, 8, 12, 30, tzinfo=UTC), 1, datetime(2026, 11, 8, 12, 30, tzinfo=UTC)),
        (datetime(2026, 10, 8, tzinfo=UTC), 3, datetime(2027, 1, 8, tzinfo=UTC)),
        (datetime(2026, 1, 31, tzinfo=UTC), 1, datetime(2026, 2, 28, tzinfo=UTC)),
        (datetime(2027, 12, 31, tzinfo=UTC), 12, datetime(2028, 12, 31, tzinfo=UTC)),
    ],
)
def test_months_are_calendar_months(start, months, end):
    assert add_months(start, months) == end


def test_a_web_hook_is_signed_over_its_time_and_raw_body():
    body = body_of("e1", "candidate.finished", {"a": 1}, datetime(2026, 10, 15, 8, tzinfo=UTC))
    expected = hmac.new(b"whsec_x", b"1760000000." + body, hashlib.sha256).hexdigest()

    assert json.loads(body) == {
        "id": "e1",
        "type": "candidate.finished",
        # When it happened: a retried event can arrive after a later one.
        "occurred_at": "2026-10-15T08:00:00+00:00",
        "timestamp": "2026-10-15T08:00:00+00:00",
        "data": {"a": 1},
    }
    assert signature(["whsec_x"], 1760000000, body) == f"t=1760000000,v1={expected}"


def test_while_a_rolled_secret_overlaps_both_sign_the_new_one_first():
    body = b'{"type":"test"}'
    new, old = (
        hmac.new(secret, b"1760000000." + body, hashlib.sha256).hexdigest()
        for secret in (b"whsec_new", b"whsec_old")
    )

    assert signature(["whsec_new", "whsec_old"], 1760000000, body) == (
        f"t=1760000000,v1={new},v1={old}"
    )


def test_a_masked_web_hook_address_keeps_only_its_site():
    assert masked("https://hooks.zapier.com/hooks/catch/1/x?k=v") == "https://hooks.zapier.com/…"
    assert masked("https://user:pass@example.com:8443/x") == "https://example.com:8443/…"
